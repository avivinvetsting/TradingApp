## Phase 2 — Detailed Accomplishments (Backtester Foundations)

This file summarizes exactly what was built in Phase 2 so a developer can understand, extend, or review the code quickly. Each section includes purpose, key APIs, behavior, and testing notes.

---

### 2.1 Data Adapters (Parquet Cache)
- Purpose: Provide deterministic, fast reads of historical bars for backtests.
- Location: `trading/data/parquet_adapter.py`
- Key API:
  - `ParquetLatestBarAdapter.latest_completed_bar(symbol: str, timeframe: str) -> Optional[Bar]`
- Expected file layout: `{base_dir}/{symbol}_{interval}.parquet` where `interval ∈ {1d,1h,1m}`.
- Schema: `symbol, end (UTC), open, high, low, close, volume`.
- Time handling: `end` coerced to timezone-aware UTC; latest bar is the max `end`.
- Tests: `tests/test_parquet_adapter.py` covers missing file and correct latest bar selection.
- Notes: Use CLI to download fixtures from yfinance if needed:
  ```bash
  python -m trading fixtures download SPY QQQ --interval 1d --start 2024-01-01 --out-dir data/cache/yf
  ```

---

### 2.2 Corporate Actions (Split Adjustment)
- Purpose: Back-adjust prices and volumes for stock splits in historical data.
- Location: `trading/data/corporate_actions.py`
- Key APIs:
  - `apply_split_adjustments(bars: pd.DataFrame, splits: Sequence[SplitEvent]) -> pd.DataFrame`
  - `fetch_yf_splits(symbol: str) -> list[SplitEvent]` (optional, uses yfinance)
- Behavior:
  - For each split with ratio r, prices prior to event are divided by the cumulative ratio; volumes multiplied.
- Tests: `tests/test_corporate_actions.py` validates pre/post-split adjustments.

---

### 2.3 Portfolio Accounting
- Purpose: Track cash, positions, realized PnL; compute unrealized PnL/equity.
- Location: `trading/portfolio/accounting.py`
- Key API:
  - `PortfolioState.apply_fill(fill: Fill, price: float, symbol: str, commission: float) -> None`
  - `PortfolioState.snapshot(as_of: datetime | None = None, marks: dict[str, float] | None = None) -> PortfolioSnapshot`
- Behavior:
  - Buy: VWAP updates average price; cash decreases by `qty*price + commission`.
  - Sell: `realized_pnl += (price - avg_price) * qty - commission`; cash increases by `qty*price - commission`; avg_price -> 0 when flat.
  - Snapshot: equity = cash + Σ(mark * qty); unrealized = Σ((mark - avg_price) * qty).
- Tests: `tests/test_portfolio_accounting.py` covers buy/sell, PnL, and cash flows.

Usage example
```python
from datetime import datetime, timezone
from trading.core.models import Fill
from trading.portfolio.accounting import PortfolioState

pf = PortfolioState(cash=10_000.0)
pf.apply_fill(
    fill=Fill(order_local_id="o1", ts=datetime.now(timezone.utc), qty=10, price=100.0, commission=1.0),
    price=100.0,
    symbol="SPY",
    commission=1.0,
)
snap = pf.snapshot(marks={"SPY": 101.0})
```

---

### 2.4 Execution Simulator & Costs
- Purpose: Deterministic fills at bar-close for market/limit orders; model slippage; optional participation cap.
- Location: `trading/execution/simulator.py`
- Key API:
  - `SimpleExecutionSimulator.simulate_fill(order: Order, bar_close: float, bar_high: float, bar_low: float, bar_volume: int) -> Optional[Fill]`
- Behavior:
  - Market: full quantity at `bar_close` ± slippage bps (directional).
  - Limit (buy): fills if `bar_low <= limit`; price = min(close, limit) ± slippage.
  - Limit (sell): fills if `bar_high >= limit`; price = max(close, limit) ± slippage.
  - Participation cap: if set, fill qty ≤ `int(bar_volume * cap)`.
  - Fill timestamps use `datetime.now(timezone.utc)`.
- Config: `ExecutionConfig` includes `slippage_bps` and `commission_fixed` (to be applied at portfolio update time).
- Tests: `tests/test_execution_simulator.py` covers slippage, limit behavior, and cap.

---

### 2.5 Risk Management (MVP)
- Purpose: Enforce basic safety checks before order submission.
- Location: `trading/risk/manager.py`
- Key APIs:
  - `BasicRiskManager.validate(proposed_order: Order) -> Optional[Order]`
  - Params: `RiskParams(max_gross_exposure, per_symbol_notional_cap, market_calendar="XNYS", daily_loss_cap=None)`
- Behavior:
  - Session gate (stubbed True for now; will integrate market calendar when live wiring lands).
  - Per-symbol notional cap for limit orders.
  - Gross exposure and daily loss cap to be enforced once portfolio exposure is wired in the loop.
- Tests: `tests/test_risk_manager.py` checks accept/reject under notional caps.

Usage example
```python
from trading.core.models import Order
from trading.risk.manager import BasicRiskManager, RiskParams

rm = BasicRiskManager(RiskParams(max_gross_exposure=100_000, per_symbol_notional_cap=5_000))
order = Order(local_id="o1", symbol="SPY", side="buy", type="limit", quantity=50, limit_price=120.0)
approved = rm.validate(order)
```

---

### Status and Next Steps
- Checklist updated in `DETAILED_PHASE_PLAN.md` (Data, CA, Portfolio, Execution/Costs, Risk, Backtest Engine, Metrics checked).
- Backtest runner added to CLI: `python -m trading backtest --config config.yaml --run-id <id>` (auto-downloads missing caches).
- Next: HTML reporting (Plotly + Jinja) to visualize equity curve, drawdowns, and orders.

---

### Commands reference
```bash
mypy .
pytest -q
python -m trading fixtures download SPY QQQ --interval 1d --start 2024-01-01
```

### Relevant config fields (YAML)
```yaml
execution:
  slippage_bps: 1
  commission_fixed: 1.0
risk:
  max_gross_exposure: 100000
  per_symbol_notional_cap: 25000
  market_calendar: XNYS
```
