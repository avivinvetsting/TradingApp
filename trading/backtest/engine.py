from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional
import json
import subprocess
import time

import pandas as pd

from trading.core.models import Bar, Order
from trading.core.contracts import Strategy
from trading.execution.simulator import SimpleExecutionSimulator, FillPolicy
from trading.portfolio.accounting import PortfolioState
from trading.risk.manager import BasicRiskManager, RiskParams
from trading.data.series_loader import load_parquet_series
from trading.backtest.metrics import compute_from_equity
from trading.util.clock import Clock, DEFAULT_CLOCK


@dataclass
class BacktestConfig:
    symbols: list[str]
    interval: str  # "1d" | "1h" | "1m"
    cache_dir: str | Path
    run_id: str
    out_dir: str | Path = "runs"
    slippage_bps: int = 1
    commission_fixed: float = 1.0
    per_symbol_notional_cap: float = 25000.0
    config_hash: Optional[str] = None
    heartbeat_every: int = 100


class BacktestEngine:
    def __init__(
        self,
        strategy_factory: Callable[[str], Strategy],
        config: BacktestConfig,
        logger: Optional[Any] = None,
        clock: Clock = DEFAULT_CLOCK,
    ) -> None:
        self.strategy_factory: Callable[[str], Strategy] = strategy_factory
        self.config = config
        # Lazy import to avoid forcing logging at import time
        try:
            # structlog logger preferred
            self._logger: Any = logger or __import__("structlog").get_logger("trading.backtest")
        except Exception:
            import logging as _logging

            self._logger = logger or _logging.getLogger("trading.backtest")
        self.sim = SimpleExecutionSimulator(
            slippage_bps=config.slippage_bps, fill_policy=FillPolicy(None)
        )
        self.portfolio = PortfolioState(cash=100000.0)
        self._clock: Clock = clock
        # Disable wall-clock session gate in backtests for determinism
        self.risk = BasicRiskManager(
            RiskParams(
                max_gross_exposure=1e9, per_symbol_notional_cap=config.per_symbol_notional_cap
            ),
            enable_session_gate=False,
        )
        self._orders: list[dict[str, Any]] = []
        self._fills: list[dict[str, Any]] = []
        self._equity: list[dict[str, Any]] = []
        self._bars: list[dict[str, Any]] = []
        # Observability accumulators
        self._orders_approved_count: int = 0
        self._bar_loop_ms: list[float] = []
        self._missing_bars_per_symbol: Dict[str, int] = {sym: 0 for sym in config.symbols}
        self._turnover_notional: float = 0.0
        self._time_in_market_bars: int = 0
        self._peak_gross_exposure: float = 0.0

    def run(self) -> None:
        self._run_start = time.perf_counter()
        out_base = Path(self.config.out_dir) / self.config.run_id
        (out_base / "reports").mkdir(parents=True, exist_ok=True)

        # Load series for each symbol
        series: Dict[str, pd.DataFrame] = {}
        missing: list[str] = []
        for sym in self.config.symbols:
            try:
                series[sym] = load_parquet_series(self.config.cache_dir, sym, self.config.interval)
            except FileNotFoundError:
                missing.append(sym)
        if not series:
            raise FileNotFoundError(
                f"No cached data found for symbols {missing} at {self.config.cache_dir}. "
                f"Generate fixtures (e.g., 'python -m trading fixtures download {' '.join(self.config.symbols)} --interval {self.config.interval} --start 2024-01-01 --out-dir {self.config.cache_dir}') or adjust cache_dir."
            )

        # Create strategies per symbol
        strategies: Dict[str, Strategy] = {
            sym: self.strategy_factory(sym) for sym in self.config.symbols
        }

        # Merge all timestamps across symbols using k-way merge to reduce memory
        import heapq

        iters: Dict[str, Any] = {sym: iter(df["end"].tolist()) for sym, df in series.items()}
        heap: list[tuple[datetime, str]] = []
        for sym, it in iters.items():
            try:
                first = next(it)
                heap.append((first, sym))
            except StopIteration:
                continue
        heapq.heapify(heap)
        all_ts: list[datetime] = []
        last_emitted: Optional[datetime] = None
        while heap:
            ts, sym = heapq.heappop(heap)
            if last_emitted is None or ts != last_emitted:
                all_ts.append(ts)
                last_emitted = ts
            # advance iterator for sym
            try:
                nxt = next(iters[sym])
                heapq.heappush(heap, (nxt, sym))
            except StopIteration:
                pass

        heartbeat_every = max(1, int(self.config.heartbeat_every))
        for idx, ts in enumerate(all_ts):
            loop_start = time.perf_counter()
            marks: Dict[str, float] = {}
            for sym, df in series.items():
                # Get row at timestamp if present
                rows = df[df["end"] == ts]
                if rows.empty:
                    self._missing_bars_per_symbol[sym] = (
                        self._missing_bars_per_symbol.get(sym, 0) + 1
                    )
                    continue
                row = rows.iloc[0]
                bar = Bar(
                    symbol=sym,
                    end=pd.to_datetime(row["end"]).to_pydatetime(),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=int(row["volume"]),
                )
                # Record bar
                self._bars.append(
                    {
                        "ts": bar.end.isoformat(),
                        "symbol": sym,
                        "open": bar.open,
                        "high": bar.high,
                        "low": bar.low,
                        "close": bar.close,
                        "volume": bar.volume,
                    }
                )
                marks[sym] = bar.close

                # Strategy decision
                order: Optional[Order] = strategies[sym].on_bar(bar)
                if order is None:
                    continue

                # Risk
                approved = self.risk.validate(order)
                if approved is None:
                    continue
                # Count orders that passed risk checks
                self._orders_approved_count += 1

                # Simulate fill
                fill = self.sim.simulate_fill(
                    order=approved,
                    bar_close=bar.close,
                    bar_high=bar.high,
                    bar_low=bar.low,
                    bar_volume=bar.volume,
                    fill_ts=bar.end,
                )
                # Record order regardless
                self._orders.append(
                    {
                        "ts": ts.isoformat(),
                        "symbol": sym,
                        "side": order.side,
                        "type": order.type,
                        "qty": order.quantity,
                        "limit": order.limit_price,
                    }
                )
                if fill is not None:
                    self._fills.append(
                        {
                            "ts": fill.ts.isoformat(),
                            "symbol": sym,
                            "qty": fill.qty,
                            "price": fill.price,
                            "commission": self.config.commission_fixed,
                        }
                    )
                    # Apply to portfolio with commission
                    self.portfolio.apply_fill(
                        fill, price=fill.price, symbol=sym, commission=self.config.commission_fixed
                    )
                    # Turnover notional accumulates absolute traded notional
                    self._turnover_notional += abs(float(fill.qty) * float(fill.price))

            snap = self.portfolio.snapshot(
                as_of=ts if isinstance(ts, datetime) else self._clock.now_utc(), marks=marks
            )
            self._equity.append(
                {
                    "ts": snap.ts.isoformat(),
                    "cash": snap.cash,
                    "equity": snap.equity,
                    "unrealized_pnl": snap.unrealized_pnl,
                    "realized_pnl": snap.realized_pnl,
                }
            )
            # Time in market: any open position across symbols
            if any(pos.qty != 0 for pos in self.portfolio.positions.values()):
                self._time_in_market_bars += 1
            # Peak gross exposure: sum absolute position market values
            gross = 0.0
            for sym, pos in self.portfolio.positions.items():
                if pos.qty == 0:
                    continue
                price = marks.get(sym, pos.avg_price)
                gross += abs(float(pos.qty) * float(price))
            if gross > self._peak_gross_exposure:
                self._peak_gross_exposure = gross
            loop_end = time.perf_counter()
            self._bar_loop_ms.append((loop_end - loop_start) * 1000.0)

            # Emit a simple heartbeat every N bars
            if idx % heartbeat_every == 0:
                try:
                    # Support both structlog and stdlib
                    try:
                        self._logger.info(
                            "heartbeat",
                            ts=snap.ts.isoformat(),
                            approved_orders=self._orders_approved_count,
                            bars_processed=idx + 1,
                        )
                    except TypeError:
                        self._logger.info(
                            "heartbeat",
                            extra={
                                "ts": snap.ts.isoformat(),
                                "approved_orders": self._orders_approved_count,
                                "bars_processed": idx + 1,
                            },
                        )
                except Exception:
                    pass

        # Write artifacts
        self._write_artifacts(out_base)

    def _write_artifacts(self, out_base: Path) -> None:
        import pyarrow as pa
        import pyarrow.parquet as pq

        def write_parquet(records: list[dict[str, Any]], name: str) -> None:
            if not records:
                return
            table = pa.Table.from_pylist(records)
            pq.write_table(table, out_base / f"{name}.parquet")

        write_parquet(self._bars, "bars")
        write_parquet(self._orders, "orders")
        write_parquet(self._fills, "fills")
        write_parquet(self._equity, "equity")

        # Compute metrics from equity
        try:
            import pyarrow.parquet as pq

            eq_path = out_base / "equity.parquet"
            if eq_path.exists():
                equity_df = pq.read_table(eq_path).to_pandas()
                metrics = compute_from_equity(equity_df, self.config.interval)
            else:
                metrics = None
        except Exception:
            metrics = None

        # Try to include git SHA
        try:
            git_sha = (
                subprocess.run(
                    ["git", "rev-parse", "HEAD"], capture_output=True, text=True
                ).stdout.strip()
                or None
            )
        except Exception:
            git_sha = None

        # Observability: counters and timers
        def _percentiles(values: list[float], ps: list[float]) -> Dict[str, float]:
            if not values:
                return {f"p{int(p*100)}": 0.0 for p in ps}
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            results: Dict[str, float] = {}
            for p in ps:
                if n == 1:
                    q = sorted_vals[0]
                else:
                    k = max(0, min(n - 1, int(round(p * (n - 1)))))
                    q = float(sorted_vals[k])
                results[f"p{int(p*100)}"] = q
            return results

        total_bars = len(self._bars)
        total_secs = max(1e-9, time.perf_counter() - self._run_start)
        bars_per_sec = float(total_bars) / float(total_secs)
        counters = {
            "bars": len(self._bars),
            "orders_proposed": len(self._orders),
            "orders_approved": self._orders_approved_count,
            "fills": len(self._fills),
        }
        timer_stats = (
            {
                "count": len(self._bar_loop_ms),
                "avg": (
                    (sum(self._bar_loop_ms) / len(self._bar_loop_ms)) if self._bar_loop_ms else 0.0
                ),
                "max": max(self._bar_loop_ms) if self._bar_loop_ms else 0.0,
                **_percentiles(self._bar_loop_ms, [0.5, 0.95]),
                "bars_per_sec": bars_per_sec,
            }
            if self._bar_loop_ms
            else {"count": 0, "avg": 0.0, "max": 0.0, "p50": 0.0, "p95": 0.0, "bars_per_sec": 0.0}
        )

        summary = {
            "run_id": self.config.run_id,
            "symbols": self.config.symbols,
            "interval": self.config.interval,
            "git_sha": git_sha,
            "config_hash": self.config.config_hash,
            "slippage_bps": self.config.slippage_bps,
            "commission_fixed": self.config.commission_fixed,
            "metrics": (
                None
                if metrics is None
                else {
                    "cagr": metrics.cagr,
                    "sharpe": metrics.sharpe,
                    "sortino": metrics.sortino,
                    "max_drawdown": metrics.max_drawdown,
                    "calmar": metrics.calmar,
                    "hit_rate": metrics.hit_rate,
                    # Additional
                    "turnover_notional": self._turnover_notional,
                    "time_in_market_ratio": (
                        float(self._time_in_market_bars) / float(len(self._equity))
                        if self._equity
                        else 0.0
                    ),
                    "peak_gross_exposure": self._peak_gross_exposure,
                }
            ),
            "observability": {
                "counters": counters,
                "timers": {
                    "bar_loop_ms": timer_stats,
                },
                "missing_bars_per_symbol": self._missing_bars_per_symbol,
            },
        }
        (out_base / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
