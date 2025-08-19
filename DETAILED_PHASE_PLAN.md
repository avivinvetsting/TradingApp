## Algorithmic Trading Bot — Phase Checklists (Context‑7 + Sequential)

Use these checklists to track progress. Check items as you complete them. Capture one-way-door decisions in `PROJECT_PLAN.md`.

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## Chronological Task Checklist — Phases 1 & 2

Use this ordered checklist to drive implementation. Check items in sequence.

### Phase 1 — Hardening (end of Week 1)

1. [x] Add `.pre-commit-config.yaml`; install hooks; run on CI
1. [x] Update `CONTRIBUTING.md` with Developer Workflow (`make ci`, branching, reviews)
1. [x] Ensure structured logging baseline (text default; JSON optional later)
1. [x] Add CODEOWNERS and PR template
1. [x] Pin critical dependencies in `pyproject.toml`; add Python version file

### Phase 2 — Hardening (final week before Phase 3)

1. [x] CI coverage gate ≥ 80% and weekly scheduled CI run
1. [x] Add risk tests: gross exposure and daily_loss_cap
1. [x] Add CLI backtest smoke test that writes artifacts to a tmp runs dir
1. [x] Enforce Parquet schema/dtype validation in loaders (UTC, numeric OHLCV)
1. [x] Add `--json-logs` flag and emit heartbeat logs in backtest loop
1. [x] Add Make targets: `make ci`, `make report RUN=<id>`, `make prune-runs`
1. [x] Add `.env.example`, `.python-version`, Dependabot; update README with runbook link
1. [x] Replace global timestamp set with k‑way merge for bar alignment (perf)
1. [x] Inject `Clock.now_utc()` and remove ad‑hoc `datetime.now` for determinism
1. [x] Record bars/sec and per‑symbol missing‑bar counters in `summary.json` and report
1. [x] Add turnover, time‑in‑market, and peak gross exposure to metrics/report
1. [ ] Add property‑based tests (portfolio invariants; simulator edge cases)
1. [ ] Add `make bench-backtest` with SLA (< 60s SPY/QQQ daily)

Note: Items 1–7 are implemented; items 8–13 are optional polish to schedule before Phase 3 if time permits.

______________________________________________________________________

## Phase 3 — Live Data & Paper Account Integration (Week 4)

- [ ] Objective: reliable paper connectivity; bars; orders; reconciliation (paper only)
- [x] Connectivity manager: health checks (connect/disconnect/status) wired via CLI dry-run
- [ ] Market data stream: `keepUpToDate` or ticks aggregated to completed bars (backtester-aligned)
- [ ] Broker adapter (paper): submit/cancel market/limit; idempotent local↔broker order id mapping
- [ ] Reconciliation: resubscribe; refresh open orders and positions; ensure no duplication
- [ ] Persistence: live orders/fills/position snapshots to SQLite/Parquet
- [ ] CLI: `trade live --config` with `--dry-run`; supports `--json-logs` and `--log-level`; emits heartbeats
- [ ] Acceptance: connects to paper; subscribes SPY/QQQ; can submit/cancel; recovers cleanly; heartbeat/backoff validated (tenacity retries with jitter); reconciliation verified after induced disconnect
- [ ] Tests: integration (dry-run, forced reconnect with mocks); contract (idempotency, reconciliation); logging shape (JSON fields: run_id, symbol, timeframe)
- [ ] Observability: heartbeat log every 60s; counters (bars/orders/latency); reconnect/failure counters

### Success Metrics (Phase 3)

- [ ] Sustained live session ≥ 30 minutes without unhandled exceptions
- [ ] Reconnect completes within ≤ 30 seconds under induced disconnect
- [ ] ≥ 25 heartbeat messages logged (60s cadence) during 30‑minute session

### Go/No‑Go — Operational Readiness (before starting live session)

- [ ] IB Gateway/TWS configured as per `PHASE3_RUNBOOK.md`; port and API enabled
- [ ] Dry‑run connectivity green for target host/port/client id
- [ ] Structured logging verified in JSON mode; log sample captured
- [ ] Reconnect test performed (forced disconnect → successful resubscribe + reconciliation)
- [ ] Persistence validated (SQLite/Parquet schema + write/read cycle)
- [ ] Alerts/notifications channel decided (even if manual for Phase 3)

### Non‑Goals (Phase 3)

- No real‑money trading (paper only)
- No options/futures support (equities/ETFs only)
- No sub‑second latencies; poll‑based loop is acceptable
- No advanced order types beyond market/limit
- No HTTP `/healthz` endpoint (use logs only); no external dashboards (HTML report only)

### Future Improvements (Phase 3+)

- Add lightweight HTTP `/healthz` endpoint with status JSON
- Export metrics via Prometheus/OpenTelemetry
- Integrate alerting channel (e.g., Slack/Email) for failures or missed heartbeats

______________________________________________________________________

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

### Non‑Goals (Phase 4)

- No production/real‑money trading yet
- No options/futures
- No portfolio margin or multi‑account orchestration

### Future Improvements (Phase 4+)

- Automated EOD report distribution (email/message)
- Additional order types (stop/stop‑limit) and policies (convert on timeout)
- Daily loss cap per‑instrument; flat‑at‑close rule

______________________________________________________________________

## Phase 5 — Stretch Enhancements & Hardening (Weeks 6–7, optional)

- [ ] Intraday backtests (1m); improved slippage models; benchmarks recorded
- [ ] Volatility-targeted sizing (ATR/EWMA) behind config flag
- [ ] Additional order types: stop/stop-limit; advanced TIF handling
- [ ] Optional live dashboard (Streamlit) for PnL/orders
- [ ] Expanded risk: per-instrument daily loss cap; flat-at-close rule
- [ ] Acceptance: performance budgets met; toggles documented; risk policies effective
- [ ] Tests: performance baselines; scenario tests for new order types/risk

______________________________________________________________________

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

### Assumptions & Constraints (all phases)

- UTC time discipline; no local timezone logic
- Single‑process orchestrator; no distributed state
- Linux/WSL2 environment; Python 3.11 pinned
- IBKR paper environment provides sufficient market data for dev

### Data Retention Policy (initial)

- Backtests: retain 7–14 days under `runs/`; prune via `trade ops prune`
- Live (paper): retain 90 days of orders/fills/positions snapshots and logs
- Never store secrets in repo; `.env` only for local development

### Incident Response (abridged)

1. Detect: heartbeat lapse or error log
1. Stabilize: auto backoff/retry; if persistently failing, stop loop safely
1. Diagnose: check connectivity, IBKR status page, credentials/ports
1. Recover: reconnect; reconcile open orders/positions; verify no duplication
1. Record: capture logs, artifacts, and timeline in issue tracker

### Verification Matrix (tests and artifacts)

- Backtester engine → `tests/test_backtest_engine.py`, `tests/test_summary_snapshot.py`; artifacts: `runs/<id>/summary.json`, `equity.parquet`, HTML report
- Portfolio accounting & costs → `tests/test_portfolio_accounting.py`
- Execution simulator → `tests/test_execution_simulator.py`
- Risk manager (caps/daily loss) → `tests/test_risk_manager.py`
- Data loaders (Parquet adapter/schema) → `tests/test_parquet_adapter.py`
- CLI (smoke/backtest) → `tests/test_cli_smoke.py`, `tests/test_cli.py`
- Reporting → `tests/test_reporting.py`
- Retention/prune → `tests/test_retention.py`
- Config settings/validators → `tests/test_config_settings.py`

### External Dependencies & Interfaces

- IBKR TWS/Gateway (paper): host `${TRADE__DATA__IB_HOST}`, port `${TRADE__DATA__IB_PORT}` (default 7497), client id `${TRADE__DATA__IB_CLIENT_ID}`
- `ib_insync` for IB API; `yfinance` optional for fixtures
- Filesystem for Parquet/HTML artifacts under `runs/` and data caches under `data/cache/`

### Live Rollback Plan (paper)

1. Stop the live loop safely on repeated failures
1. Cancel open limit orders; verify broker state
1. Reconcile positions; ensure no unintended exposure
1. Archive logs and artifacts; file incident with timeline

### Acceptance Test Procedures (ATPs)

Phase 3 (Live paper connectivity)

1. Prepare environment: `.env` set for IB host/port/client id; TWS/Gateway running with API enabled
1. Dry‑run: `python -m trading live --config config.example.yaml --dry-run` → expect connect/disconnect success
1. Live session (paper): start loop; verify heartbeats every 60s; observe counters increasing
1. Induce disconnect (stop TWS for ~15s); restart TWS → system reconnects within ≤ 30s; subscriptions restored; no duplicate state
1. Persistence: verify SQLite/Parquet snapshots created/readable; logs contain reconnect/backoff entries

Phase 4 (First paper trade)

1. Start live loop (paper) with tiny size policy; verify heartbeats and no errors
1. Submit a small limit order (via strategy or manual trigger if available); verify order submission logged
1. Verify fills ledger written; portfolio equity/PnL updated; commission applied
1. Restart process; verify reconciliation (open orders/positions) and no duplication
1. Generate EOD report; archive artifacts; validate completeness (orders, fills, PnL, positions)

### Configuration Matrix (required keys)

- `timeframe` ("1d"|"1h"|"1m") — normalized; validated
- `symbols` (non‑empty list of tickers)
- `data.cache_dir` (writable path)
- `data.ib_host` / `data.ib_port` / `data.ib_client_id` (Phase 3+)
- `risk.max_gross_exposure` (≥ 0), `risk.per_symbol_notional_cap` (≥ 0), `risk.daily_loss_cap` (≥ 0 or unset)
- `execution.slippage_bps`, `execution.commission_fixed`

### Release Checklist

- Branch up to date with `main`; CI green (unit + integration)
- Coverage ≥ 80%; lint/type/security scans pass
- CHANGELOG/Decision Log updated; tag created if applicable
- Runbook (`PHASE3_RUNBOOK.md`) reviewed; rollback plan verified

### Glossary

- Bar: OHLCV record for a fixed interval ending at `end` (UTC)
- Heartbeat: periodic log indicating liveness with counters
- Run ID: unique identifier (UUIDv4 or provided) for a run’s artifacts directory
- Reconciliation: process of aligning local state with broker (orders, positions) after (re)connect

______________________________________________________________________

## Notes & Decisions (current)

- Timeframe: start daily; plan to add 1h/1m later
- Logging format: default text; JSON optional later
- Run-id: default UUIDv4; CLI accepts `--run-id`
- Retention: backtests short (e.g., 7–14 days), live runs longer (e.g., 90+ days); manage via `python -m trading ops prune`
- TWS connection is required starting Phase 3 (live integration); not needed for Phase 1–2

______________________________________________________________________

## Phase 2 — Accomplishments

- Data: Parquet adapter for latest bars; series loader for full symbol datasets; CLI auto-download for missing caches
- Corporate actions: Split adjustment for prices/volume; dividends deferred
- Portfolio: In-memory accounting of cash/positions; realized and unrealized PnL; snapshot equity series
- Execution: Deterministic simulator for market/limit; slippage bps; optional participation cap
- Costs: Fixed commission configured; applied in backtest when updating portfolio
- Risk: Per-symbol notional cap for limit orders; session gate stub (calendar wiring later)
- Backtest engine: Bar-close loop over multiple symbols; ledgers (orders, fills, equity) written as Parquet; metrics computed and embedded in `summary.json`
- CLI: `python -m trading backtest --config config.yaml --run-id <id>` runs end-to-end and auto-downloads missing caches
