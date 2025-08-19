## Algorithmic Trading Bot — Phase Checklists (Context‑7 + Sequential)

Use these checklists to track progress. Check items as you complete them. Capture one-way-door decisions in `PROJECT_PLAN.md`.

---

## Phase 1 — Core Infrastructure & Foundation (Week 1)

- [x] Objective agreed: scaffold with contracts, config, CLI, logging, CI
- [x] Python 3.11 venv ready; repo initialized; CI enabled
- [x] Package structure under `trading/` (core/config/strategy/indicators/data/broker/portfolio/execution/backtest/live/observability)
- [x] Contracts (ABCs): DataAdapter, BrokerAdapter, Strategy, RiskManager, ExecutionEngine, Portfolio
- [x] Domain models: Instrument, Bar, Order, Fill, Position, PortfolioSnapshot
- [x] Config loader (pydantic v2, YAML + env overlays, `.env` support)
- [x] Strategy/indicator registry with decorator-based registration
- [x] CLI: `python -m trading` with `trade plan|backtest|live` (stubs)
- [x] Logging helper and run-id propagation pattern
- [x] Tooling: `ruff`, `black`, `mypy`, `pytest`, pre-commit, GitHub Actions CI (workflow added)
- [x] Example strategies registered: `momentum`, `ma_crossover` (placeholders)
- [x] Acceptance: CLI help shows; config resolves; registry lists; CI green; reproducible local runs
- [x] Tests: unit for config/registry/models; lint/type gates pass

---

## Phase 2 — Backtester MVP (Weeks 2–3)

- [x] Objective agreed: deterministic bar-based backtester with accounting, costs, risk, reporting
- [x] Data adapters: IB historical pull (batched) + local Parquet cache; CSV/Parquet loader
- [x] Corporate actions adjuster (splits); dividends pending; docs on limitations
- [x] Split adjuster implemented for prices/volume; tests added
- [x] Portfolio accounting: cash, positions, unrealized/realized PnL, equity curve
- [x] Portfolio accounting: cash, positions, realized/unrealized PnL; snapshot tests
- [x] Costs: fixed commission; slippage bps
- [x] Costs: slippage bps simulated; fixed commission added to config
- [x] Execution simulator: market/limit; optional partial fills
- [x] Execution simulator: market/limit with participation cap; tests
- [x] Risk manager: per-symbol notional cap; max gross exposure; market-hours gate; daily kill-switch
- [x] Backtest engine: bar-close evaluation; ledgers (bars/orders/fills/equity); JSON summary (git SHA + config hash)
- [x] Backtest engine: bar-close evaluation; writes orders/fills/equity parquet + JSON summary
- [x] Reporting: HTML via Plotly+Jinja (equity, drawdown); metrics included in summary.json
- [x] Metrics: compute CAGR/Sharpe/Sortino/maxDD/Calmar/hit-rate; included in summary.json
- [x] Acceptance: SPY/QQQ backtest produces metrics + HTML; artifacts under `runs/{run_id}/`
- [x] Tests: unit (portfolio/costs/risk/CA); integration (fixture backtest); regression (summary snapshot)
- [x] Observability: counters for bars/orders; latency timers

---

## Phase 3 — Live Data & Paper Account Integration (Week 4)

- [ ] Objective agreed: reliable paper connectivity; bars; orders; reconciliation
- [x] Connectivity manager: health checks (connect/disconnect/status) wired via CLI dry-run
- [ ] Market data stream: `keepUpToDate` or ticks aggregated to completed bars (backtester-aligned)
- [ ] Broker adapter (paper): submit/cancel market/limit; idempotent local↔broker order id mapping
- [ ] Reconciliation: resubscribe; refresh open orders and positions; ensure no duplication
- [ ] Persistence: live orders/fills/position snapshots to SQLite/Parquet
- [ ] CLI: `trade live --config` with `--dry-run`; supports `--json-logs` and `--log-level`; emits heartbeats
- [ ] Acceptance: connects to paper; subscribes SPY/QQQ; can submit/cancel; recovers cleanly; heartbeat/backoff validated (tenacity retries with jitter); reconciliation verified after induced disconnect
- [ ] Tests: integration (dry-run, forced reconnect with mocks); contract (idempotency, reconciliation); logging shape (JSON fields: run_id, symbol, timeframe)
- [ ] Observability: optional `/healthz` or periodic heartbeat log; counters (bars/orders/latency); reconnect/failure counters

### Go/No‑Go — Operational Readiness (before starting live session)

- [ ] IB Gateway/TWS configured as per `PHASE3_RUNBOOK.md`; port and API enabled
- [ ] Dry‑run connectivity green for target host/port/client id
- [ ] Structured logging verified in JSON mode; log sample captured
- [ ] Reconnect test performed (forced disconnect → successful resubscribe + reconciliation)
- [ ] Persistence validated (SQLite/Parquet schema + write/read cycle)
- [ ] Alerts/notifications channel decided (even if manual for Phase 3)

---

## Phase 4 — First Paper Trade (Week 5)

- [ ] Orchestrator: time-driven polling → Strategy → Risk → Execution
- [ ] Order lifecycle: TIF DAY; unfilled policy (timeout cancel/convert) via config
- [ ] Precision/rounding: enforce IBKR increments for price/size
- [ ] Daily report: orders, fills, PnL, positions; per `run_id`
- [ ] Runbook: start/stop/recovery steps; restart idempotency verified
- [ ] Acceptance: at least one filled paper order; accurate ledgers; EOD report; restart without duplication; no unhandled exceptions
- [ ] Tests: dry-run smoke; live paper test with tiny size; latency SLO observed (bar close → submit ≤ 2s for 1m)
 - [ ] Quality gates: logs uniform (JSON/text), daily report completeness check, CI green incl. integration

### Exit Checklist (end of Phase 4)

- [ ] At least one placed and filled paper order with full lifecycle events persisted
- [ ] EOD report archived and shared (contains orders, fills, PnL, positions)
- [ ] Restart test: stop/start without duplication; open orders reconciled; positions match broker
- [ ] Incident drill: simulate broker outage for 2–5 minutes → system recovers with backoff

---

## Phase 5 — Stretch Enhancements & Hardening (Weeks 6–7, optional)

- [ ] Intraday backtests (1m); improved slippage models; benchmarks recorded
- [ ] Volatility-targeted sizing (ATR/EWMA) behind config flag
- [ ] Additional order types: stop/stop-limit; advanced TIF handling
- [ ] Optional live dashboard (Streamlit) for PnL/orders
- [ ] Expanded risk: per-instrument daily loss cap; flat-at-close rule
- [ ] Acceptance: performance budgets met; toggles documented; risk policies effective
- [ ] Tests: performance baselines; scenario tests for new order types/risk

---

## Cross-Phase Checklists

Start-of-Phase

- [ ] Decision Log updated; open questions reviewed
- [ ] CI green on `main`; working branch created
- [ ] Risks and NFRs re-evaluated for the phase
- [ ] Confirm: timeframe (start daily; add 1h/1m later), logging (text; JSON optional), run-id (UUIDv4; CLI override), retention policy via `trade ops prune`

End-of-Phase

- [ ] Acceptance criteria met; DoD satisfied
- [ ] Artifacts archived under `runs/{run_id}/`
- [ ] README and `PROJECT_PLAN.md` updated
- [ ] Open questions answered or moved forward

### Quality Gates (all phases)

- [ ] Test coverage ≥ 80% and stable CI (unit + integration)
- [ ] Structured logging uniform: JSON option; key fields bound (run_id, symbols, interval)
- [ ] No bare `except Exception` without logging and context; error paths tested
- [ ] Data I/O validation: Parquet/CSV schema and dtypes validated at load; UTC timestamps monotonic
- [ ] Security/dev tooling: pre-commit hooks run clean; lint/type checks pass; security scans (bandit, pip-audit) clean or triaged
- [ ] Dependency hygiene: dependabot/renovate enabled; Python version pinned
- [ ] Reproducibility: deterministic backtest outputs given same cache and config hash; artifacts + report generated

### Hardening Backlog (optional but recommended)

- [ ] Performance: k‑way timestamp merge in backtester; streamed/partitioned Parquet writes
- [ ] Time: inject clock abstraction; remove direct `datetime.now()` usage for determinism
- [ ] Data: add schema version metadata to Parquet and validate on read
- [ ] Tests: property‑based tests for portfolio and execution edge cases; logging shape tests
- [ ] Live: add retry/backoff with jitter to all broker/data calls; chaos/reconnect tests
- [ ] Tooling: pre-commit config standardized; CI caches and Codecov guard; Dependabot for actions

---

## Notes & Decisions (current)

- Timeframe: start daily; plan to add 1h/1m later
- Logging format: default text; JSON optional later
- Run-id: default UUIDv4; CLI accepts `--run-id`
- Retention: backtests short (e.g., 7–14 days), live runs longer (e.g., 90+ days); manage via `python -m trading ops prune`
- TWS connection is required starting Phase 3 (live integration); not needed for Phase 1–2

---

## Phase 2 — Accomplishments

- Data: Parquet adapter for latest bars; series loader for full symbol datasets; CLI auto-download for missing caches
- Corporate actions: Split adjustment for prices/volume; dividends deferred
- Portfolio: In-memory accounting of cash/positions; realized and unrealized PnL; snapshot equity series
- Execution: Deterministic simulator for market/limit; slippage bps; optional participation cap
- Costs: Fixed commission configured; applied in backtest when updating portfolio
- Risk: Per-symbol notional cap for limit orders; session gate stub (calendar wiring later)
- Backtest engine: Bar-close loop over multiple symbols; ledgers (orders, fills, equity) written as Parquet; metrics computed and embedded in `summary.json`
- CLI: `python -m trading backtest --config config.yaml --run-id <id>` runs end-to-end and auto-downloads missing caches
