## Algorithmic Trading Bot: Project Plan (IBKR, Python)

### Project Context
- **Language/Env**: Python 3.11.x (pin in CI; broadest wheel support for deps)
- **Broker**: Interactive Brokers (TWS/IB Gateway), paper trading first
- **Markets**: US index ETFs initially (e.g., SPY, QQQ, DIA, IWM); expand to equities later
- **Style**: Long-only; bar-close decisions; speed prioritized over high-fidelity initially
- **Data**: Start with IB historical; begin local caching; handle corporate actions (splits/dividends)
- **Storage**: Local-first (Parquet/SQLite); detailed logs and ledgers retained
- **Reporting**: HTML and notebook reports; web dashboard later

### Guiding Principles (context-aware, sequential delivery)
- Optimize for correctness and simplicity first; add sophistication only when a real limitation is encountered.
- Prefer explicit contracts and small, composable components over monoliths.
- Make state and decisions observable by default (logs, metrics, artifacts) to speed feedback.
- One-way door decisions recorded in a decision log; everything else is reversible with small edits.
- Each milestone is shippable and independently valuable; avoid cross-milestone coupling.

### Recommended IBKR Market Data (initial)
- Use delayed data for development if needed.
- For live paper decisioning on US ETFs/equities, plan to subscribe to Level I US equities/ETFs (e.g., US Equity and Options Value Bundle). This enables real-time quotes and top-of-book needed for timely signals.

---

## Milestone 1 — Core Infrastructure & Foundation (Week 1)

### Deliverables
- **Repo scaffold** with clean package layout:
  - `trading/` with subpackages: `core`, `config`, `strategy`, `indicators`, `data`, `broker`, `portfolio`, `execution`, `backtest`, `live`, `observability`.
- **Configuration**: Pydantic Settings; layered YAML + env; `.env` support.
- **Contracts** (ABCs): `DataAdapter`, `BrokerAdapter`, `Strategy`, `RiskManager`, `ExecutionEngine`, `Portfolio`.
- **Domain models**: `Instrument`, `Bar`, `Order`, `Fill`, `Position`, `PortfolioSnapshot`.
- **Plugin registry**: Decorator-based registration for strategies and indicators.
- **CLI**: `trade plan`, `trade backtest`, `trade live` stubs via `typer`.
- **Logging**: Structured, human-readable logs with run-id tagging.
- **Quality/CI**: `pyproject.toml` with deps; `ruff`, `black`, `pytest`, `mypy`; GitHub Actions workflow.
- **Example strategies**: Momentum and MA-crossover (long-only) stubs with config.

### Acceptance Criteria
- `python -m trading --help` shows CLI.
- YAML + env config loads and resolves.
- Registry lists available strategies.
- CI green: lint, type-check, and unit tests pass.
 - Reproducible local runs given same config and cache (document seed/clock assumptions).

---

## Milestone 2 — Backtester MVP (Weeks 2–3)

### Scope
- Deterministic, single-process, bar-based engine for speed; bar-close evaluation; long-only; single strategy across a small symbol set.

### Deliverables
- **Data adapters**:
  - IB historical pulls via `ib_insync` (batched), with local Parquet cache.
  - CSV/Parquet loader that reads cache and normalizes to a unified `Bar` schema.
- **Corporate actions (CA)**:
  - Adjuster to apply split/dividend factors to historical bars.
  - Factor sourcing via best-effort provider (e.g., Yahoo) with local cache; documented limitations.
- **Portfolio & costs**:
  - Portfolio accounting (cash, positions, realized/unrealized PnL, equity curve).
  - Costs: fixed commission per order; slippage in basis points.
- **Execution simulator**:
  - Market and limit orders; optional simple partial fill (volume cap) toggle.
- **Risk (MVP)**:
  - Pre-trade checks: per-symbol notional cap, max gross exposure, market-hours gate, daily kill-switch.
- **Metrics & reports**:
  - Metrics: CAGR, Sharpe/Sortino, max drawdown, Calmar, hit rate, exposure.
  - Artifacts: Parquet ledgers (bars, orders, fills, equity); JSON summary.
  - HTML report (Plotly + Jinja) and a Jupyter notebook template.

### Acceptance Criteria
- Backtest runs on SPY/QQQ (daily or 1m) producing metrics and HTML report.
- Deterministic results given same cache and config.
- Risk checks prevent rule violations; kill-switch halts the run when triggered.
 - Artifacts (bars, orders, fills, equity) written with immutable run-id directory; JSON summary includes git SHA and config hash.

### Quality Gates for Milestone 2
- Coverage ≥ 80% (unit); integration tests green
- Structured logs available (text + JSON) with `run_id`, `symbols`, `interval`
- Parquet loader validates schema/dtypes; UTC timestamps monotonic; errors clear
- CI includes lint/type/security scans; weekly scheduled run; dependency updates enabled

---

## Milestone 3 — Live Data & Paper Account Integration (Week 4)

### Scope
- Paper account connectivity; resilient streaming and order handling with auto-reconnect.

### Deliverables
- **IB connectivity**:
  - Connection manager with health checks and exponential backoff.
  - Market data: `reqHistoricalData(keepUpToDate)` or tick streams aggregated into bars aligned with backtester format.
- **Broker adapter (paper)**:
  - Place/cancel market and limit orders; idempotent local↔broker order id mapping.
  - Execution stream; reconcile open orders and positions on reconnect.
- **State & ledgers**:
  - SQLite or local Parquet for live orders/fills/position snapshots.
- **Risk gate (live)**:
  - Same pre-trade policies as backtest; US market calendar gating.
- **CLI**:
  - `trade live --config` runs the live loop; dry-run toggle for validation.

### Acceptance Criteria
- Connects to IB paper; subscribes to SPY/QQQ; streams live bars.
- Can submit and cancel a test limit order; events logged and persisted.
- Disconnect/reconnect recovers subscriptions and reconciles state without duplication.
 - Health endpoint or heartbeat log cadence demonstrates liveness; exponential backoff respected under induced failures.

---

## Milestone 4 — The First Paper Trade (Week 5)

### Scope
- End-to-end automated trade in paper account using a configured strategy at bar close.

### Deliverables
- **Orchestrator**:
  - Loads strategy config; starts data stream; invokes strategy on bar-close; routes through risk and execution to broker.
- **Order lifecycle**:
  - Defaults: TIF `DAY`; price/size precision per instrument; safe rounding.
  - Policy for unfilled limits (timeout → cancel or convert to market based on config).
- **Reporting**:
  - Daily HTML report (orders, fills, PnL); artifacts written per run id.
- **Runbook**:
  - Checklist to start/stop, verify health, and recover from issues.

### Acceptance Criteria
- At least one automated order is placed and filled in paper.
- Orders/fills ledgers and PnL updated; report generated.
- On restart, system reconciles and resumes without duplicating actions.
 - End-of-day report includes positions, cash, PnL, and outstanding orders; no unhandled exceptions during the session.

---

## Live Orchestrator — Time-Driven Main Loop (Design)

### Goals
- Simple, time-driven polling (e.g., check for a completed bar every minute)
- Clear flow: new bar -> Strategy -> Risk -> Execution
- The loop itself is stateless; state lives in portfolio/broker/strategy
- Resilient: catch and log exceptions without crashing

### Logic Flow
1. Wait until market session is open (market clock gate).
2. For each symbol, poll the data adapter for the latest completed bar for the configured timeframe.
3. If a bar is new since the last processed timestamp, pass it to the `Strategy`.
4. If the strategy returns a proposed `Order`, pass to `RiskManager.validate`.
5. If approved, submit via `ExecutionEngine` to the broker.
6. Repeat at a configurable poll interval (default 1s).

### Minimal Outline (Python)
```python
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Sequence

class Bar: ...  # symbol, end (bar close), ohlcv
class Order: ...
class Strategy:
    def on_bar(self, bar: Bar) -> Optional[Order]: ...
class RiskManager:
    def validate(self, proposed_order: Order) -> Optional[Order]: ...
class ExecutionEngine:
    def submit(self, order: Order) -> None: ...
class DataAdapter:
    def latest_completed_bar(self, symbol: str, timeframe: str) -> Optional[Bar]: ...
class MarketClock:
    def is_session_open(self, now: datetime) -> bool: ...
    def next_session_open(self, now: datetime) -> datetime: ...

class LiveOrchestrator:
    def __init__(
        self,
        symbols: Sequence[str],
        timeframe: str,
        data_adapter: DataAdapter,
        strategy: Strategy,
        risk_manager: RiskManager,
        execution_engine: ExecutionEngine,
        market_clock: MarketClock,
        logger: Optional[logging.Logger] = None,
        poll_interval_seconds: float = 1.0,
    ) -> None:
        self.symbols = list(symbols)
        self.timeframe = timeframe
        self.data_adapter = data_adapter
        self.strategy = strategy
        self.risk_manager = risk_manager
        self.execution_engine = execution_engine
        self.market_clock = market_clock
        self.logger = logger or logging.getLogger("orchestrator")
        self.poll_interval_seconds = poll_interval_seconds
        self._last_bar_end: Dict[str, datetime] = {}

    def run_forever(self) -> None:
        self.logger.info("LiveOrchestrator started", extra={"symbols": self.symbols, "timeframe": self.timeframe})
        while True:
            now = datetime.utcnow()
            if not self.market_clock.is_session_open(now):
                wake = self.market_clock.next_session_open(now) + timedelta(seconds=2)
                time.sleep(max(0.5, (wake - now).total_seconds()))
                continue

            for symbol in self.symbols:
                try:
                    bar = self.data_adapter.latest_completed_bar(symbol, self.timeframe)
                except Exception as exc:
                    self.logger.exception("Data adapter error", extra={"symbol": symbol, "error": str(exc)})
                    continue

                if bar is None:
                    continue

                last_end = self._last_bar_end.get(symbol)
                if last_end is not None and bar.end <= last_end:
                    continue

                try:
                    proposed = self.strategy.on_bar(bar)
                except Exception as exc:
                    self.logger.exception("Strategy error", extra={"symbol": symbol, "bar_end": getattr(bar, 'end', None), "error": str(exc)})
                    self._last_bar_end[symbol] = bar.end
                    continue

                if proposed is None:
                    self._last_bar_end[symbol] = bar.end
                    continue

                try:
                    approved = self.risk_manager.validate(proposed)
                except Exception as exc:
                    self.logger.exception("RiskManager error", extra={"symbol": symbol, "error": str(exc)})
                    self._last_bar_end[symbol] = bar.end
                    continue

                if approved is None:
                    self.logger.info("Order rejected by risk", extra={"symbol": symbol})
                    self._last_bar_end[symbol] = bar.end
                    continue

                try:
                    self.execution_engine.submit(approved)
                    self.logger.info("Order submitted", extra={"symbol": symbol})
                except Exception as exc:
                    self.logger.exception("ExecutionEngine error", extra={"symbol": symbol, "error": str(exc)})

                self._last_bar_end[symbol] = bar.end

            time.sleep(self.poll_interval_seconds)
```

Implementation notes
- Keep the orchestrator free of business state; use it only to route work.
- `DataAdapter`, `RiskManager`, `ExecutionEngine`, and `Strategy` are responsible for reconnects, idempotency, and persistence as needed.
- Log exceptions; never let the loop crash. Consider process-level watchdog/supervisor for production.

Observability hooks
- Emit structured logs with a `run_id`, `symbol`, and `bar_end` where applicable.
- Export basic counters (bars processed, orders proposed/approved/submitted) and timers (latency between bar close and submit).
- Add an optional lightweight HTTP health endpoint for liveness/readiness when running long-lived processes.

## Stretch Enhancements (Weeks 6–7, optional)
- Intraday 1m backtests for ETFs; improved slippage models.
- Volatility-targeted position sizing (e.g., ATR/EWMA) as an option.
- Additional order types: stop/stop-limit; enhanced time-in-force handling.
- Simple web dashboard (Streamlit) to visualize live PnL and orders.
- Improved corporate actions via a dedicated CA provider if required.
- Expanded risk: per-instrument daily loss cap; flat-at-close rule.

---

## Week-by-Week Timeline

- **Week 1 — Core foundation**
  - Scaffold repo, config system, ABCs/models, registry, CLI, logging, CI.
  - Deliverable: runnable CLI, strategy listing, CI green.

- **Week 2 — Backtester MVP (part 1)**
  - IB historical pull + local cache; portfolio accounting; market orders; fixed commission/slippage.

- **Week 3 — Backtester MVP (part 2)**
  - Limit orders, simple partial fills; metrics; HTML report; CA adjuster; risk checks.
  - Deliverable: full backtest on SPY/QQQ with HTML report and ledgers.

- **Week 4 — Live integration (paper)**
  - IB paper connection; live bar aggregation; broker adapter (market/limit); reconnection; persistence.
  - Deliverable: subscribe to live bars; place/cancel test orders; state recovery works.

- **Week 5 — First paper trade**
  - Orchestrate strategy at bar-close; risk checks; order lifecycle; daily report; runbook.
  - Deliverable: first automated filled trade in paper; reports and ledgers produced.

- **Weeks 6–7 — Stretch and hardening (optional)**
  - Intraday backtests; volatility sizing; extra order types; Streamlit dashboard; risk expansions.

---

## Technology Stack
- **Data & IB**: `ib_insync`, `pandas`, `numpy`, `pyarrow` (Parquet), `pandas-market-calendars`; optional `yfinance` for CA factors.
- **Config & CLI**: `pydantic` v2, `typer`, `.env` via `python-dotenv`.
- **Engines**: Synchronous backtest loop; `asyncio` for live.
- **QA/DevEx**: `pytest`, `mypy`, `ruff`, `black`, pre-commit hooks; GitHub Actions CI.
- **Reporting**: Plotly + Jinja HTML; Jupyter notebooks template.
- **Storage**: Parquet for artifacts; SQLite for live state.

Suggested additions
- **Logging**: `structlog` for structured logs; fall back to stdlib logging if preferred.
- **Retry/Backoff**: `tenacity` for consistent retry policies.
- **Time**: `pendulum` for timezones (optional) or stick to `datetime` UTC-only discipline.

---

## Non-Functional Requirements
- **Reliability**: Process must handle transient broker/data failures without manual intervention; no data/order duplication after reconnect.
- **Determinism (backtest)**: Given the same inputs and config hash, results must be byte-identical.
- **Latency budget (live)**: From bar close to order submission ≤ 2 seconds for 1m bars on local machine.
- **Observability**: All runs logged with `run_id`; artifacts, metrics and HTML report required for any strategy evaluation.
- **Security**: IB credentials and API keys never logged; secrets via environment or OS keyring; repo contains no plaintext secrets.
- **Portability**: Linux-first; scripts should also run under WSL2 on Windows (documented).

## Testing Strategy
- **Unit tests**: Contracts for `DataAdapter`, `Strategy`, `RiskManager`, `ExecutionEngine`, portfolio math, CA adjuster.
- **Integration tests**: File-backed data adapter; order simulator; end-to-end backtest with a known dataset and golden metrics.
- **Live dry-run test**: Connect to IB paper in dry-run mode, stream bars for a few minutes, assert heartbeats and reconnection.
- **Regression guardrails**: Snapshot JSON summary and key metrics with tolerances; config hash embedded in artifacts.

## Configuration Layout Example
```yaml
run_id: ${RUN_ID}
timeframe: "1D"  # or "1m"
symbols: ["SPY", "QQQ"]
data:
  source: "ib"
  cache_dir: "./data/cache"
  ib:
    host: "127.0.0.1"
    port: 7497
    client_id: 42
broker:
  paper: true
risk:
  max_gross_exposure: 100000
  per_symbol_notional_cap: 25000
execution:
  default_order_type: "limit"
  slippage_bps: 1
strategy:
  name: "ma_crossover"
  params:
    fast: 20
    slow: 50
```

## Minimal Data Schemas (v0)
- **Bar**: `symbol:str, end:datetime(UTC), open:float, high:float, low:float, close:float, volume:int`
- **Order**: `broker_id:Optional[str], local_id:str, symbol:str, side:buy|sell, type:market|limit, quantity:int, limit_price:Optional[float], tif:str("DAY")`
- **Fill**: `order_local_id:str, ts:datetime, qty:int, price:float, commission:float`
- **Position**: `symbol:str, qty:int, avg_price:float`
- **PortfolioSnapshot**: `ts:datetime, cash:float, equity:float, unrealized_pnl:float, realized_pnl:float`

## Operational Runbook (abridged)
1. Start IB Gateway/TWS (paper) and verify connection port.
2. Export environment: `.env` or shell vars with credentials/ports.
3. Warm the cache (optional): run historical pull for target symbols.
4. Backtest: `trade backtest --config config.yaml` → inspect HTML and metrics.
5. Live dry-run: `trade live --config config.yaml --dry-run` for 5–10 minutes.
6. Live paper: `trade live --config config.yaml` and monitor heartbeats, daily report.
7. Shutdown: use CLI stop, verify ledgers written and positions reconciled.

## Definition of Done (per milestone)
- All acceptance criteria met and demonstrated.
- CI green (lint, mypy, unit/integration tests).
- Docs updated: README snippet, config example, runbook notes.
- Artifacts and reports generated for a sample run and archived.

## Risk & Mitigations
- **Python 3.13 compatibility (ib_insync)**: Verify early; if issues, use Python 3.12 via `pyenv`.
- **IB rate limits & market data**: Throttle requests; aggressively cache historical data; prefer batched pulls.
- **Corporate actions accuracy**: Start with best-effort factors; validate spot checks; upgrade provider if discrepancies appear.
- **Reconnection & idempotency**: Implement order id mapping; reconcile open orders/positions on startup; backoff + resubscribe.

Additional risks
- **Clock/Timezone drift**: Ensure system clock sync; use UTC everywhere; handle DST via calendar library.
- **Precision/rounding**: Price/size rounding must match IBKR rules; reject orders that violate min increments.
- **Data gaps**: Handle missing bars gracefully; skip rather than extrapolate; log anomalies.
- **Out-of-hours behavior**: Market-hours gate prevents accidental after-hours orders.
- **Resource limits**: Memory/CPU ceilings for 1m aggregation; monitor and optimize hotspots.

---

## Next Actions
- Initialize repository and implement Milestone 1 skeleton.
- Confirm IBKR paper account access and TWS/IB Gateway setup.
- Decide daily vs 1m bars for initial backtests (recommend start with daily for speed, then 1m).
 - Add CI with Python 3.11 and cacheable dependency install; enable `ruff`, `black`, `mypy`.
 - Create a sample `config.example.yaml` based on the layout above.

## Open Questions
- Preferred initial timeframe: daily for speed or 1m for realism?
- Which risk limits are acceptable for paper (caps, kill-switch thresholds)?
- Any constraints on running under WSL2 vs native Linux/Mac?

## Decision Log (to be populated)
- [x] 2025-08-18 — Pin Python version to 3.11; logging format default text (JSON optional later); run-id default UUIDv4 for now; initial timeframe daily candles with intent to move to 1h/1m later; artifact retention TBD (short for backtests, longer for live long runs).
