from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional
import json

import pandas as pd

from trading.core.models import Bar, Order
from trading.core.contracts import Strategy
from trading.execution.simulator import SimpleExecutionSimulator, FillPolicy
from trading.portfolio.accounting import PortfolioState
from trading.risk.manager import BasicRiskManager, RiskParams
from trading.data.series_loader import load_parquet_series
from trading.backtest.metrics import compute_from_equity


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


class BacktestEngine:
    def __init__(self, strategy_factory: Callable[[str], Strategy], config: BacktestConfig) -> None:
        self.strategy_factory: Callable[[str], Strategy] = strategy_factory
        self.config = config
        self.sim = SimpleExecutionSimulator(
            slippage_bps=config.slippage_bps, fill_policy=FillPolicy(None)
        )
        self.portfolio = PortfolioState(cash=100000.0)
        self.risk = BasicRiskManager(
            RiskParams(
                max_gross_exposure=1e9, per_symbol_notional_cap=config.per_symbol_notional_cap
            )
        )
        self._orders: list[dict[str, Any]] = []
        self._fills: list[dict[str, Any]] = []
        self._equity: list[dict[str, Any]] = []

    def run(self) -> None:
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

        # Merge all timestamps across symbols
        all_ts = sorted(set(ts for df in series.values() for ts in df["end"].tolist()))

        for ts in all_ts:
            marks: Dict[str, float] = {}
            for sym, df in series.items():
                # Get row at timestamp if present
                rows = df[df["end"] == ts]
                if rows.empty:
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
                marks[sym] = bar.close

                # Strategy decision
                order: Optional[Order] = strategies[sym].on_bar(bar)
                if order is None:
                    continue

                # Risk
                approved = self.risk.validate(order)
                if approved is None:
                    continue

                # Simulate fill
                fill = self.sim.simulate_fill(
                    order=approved,
                    bar_close=bar.close,
                    bar_high=bar.high,
                    bar_low=bar.low,
                    bar_volume=bar.volume,
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

            snap = self.portfolio.snapshot(
                as_of=ts if isinstance(ts, datetime) else datetime.now(timezone.utc), marks=marks
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

        summary = {
            "run_id": self.config.run_id,
            "symbols": self.config.symbols,
            "interval": self.config.interval,
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
                }
            ),
        }
        (out_base / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
