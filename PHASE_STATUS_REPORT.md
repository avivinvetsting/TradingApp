## Project Phases Status Report (Phases 1–3)

This report summarizes what is implemented vs. pending across Phases 1, 2, and 3, what should be validated, and notable problems solved and remaining. It also contains a quickstart and a concrete, beginner‑friendly task list with file paths and commands. Sources: `PROJECT_PLAN.md`, `DETAILED_PHASE_PLAN.md`, and the codebase.

### Quickstart (beginner‑friendly)
- Install dev dependencies and hooks (WSL venv active):
  - `make setup`
  - `pre-commit install && pre-commit run --all-files`
- Run a backtest end‑to‑end:
  - `python -m trading backtest --config config.example.yaml --run-id test-run`
  - Generate HTML: `make report RUN=test-run`
  - Open: `runs/test-run/reports/report.html`
- Run live dry‑run connectivity:
  - Ensure IB TWS/Gateway is running (paper), API enabled, host/port/client configured in `.env` or YAML (`TRADE__DATA__IB_HOST|PORT|CLIENT_ID`)
  - `python -m trading live --config config.example.yaml --dry-run --json-logs`
- CI locally:
  - `make ci`

### Code map (where things live)
- Backtester engine and metrics: `trading/backtest/engine.py`, `trading/backtest/metrics.py`
- Reporting (HTML): `trading/reporting/report.py`, `trading/reporting/report.html.j2`
- Execution simulator: `trading/execution/simulator.py`
- Portfolio accounting: `trading/portfolio/accounting.py`
- Risk checks: `trading/risk/manager.py`
- Data series (Parquet): `trading/data/series_loader.py`, fixtures: `trading/data/fixtures.py`
- Config: `trading/config/settings.py`
- CLI: `trading/cli.py`
- Live connectivity (IBKR): `trading/live/connection.py`
- Logging helper: `trading/observability/logging.py`

### Phase 1 — Core Infrastructure & Foundation
- DONE (per `DETAILED_PHASE_PLAN.md`):
  - Project scaffold and packages under `trading/`
  - Contracts and domain models
  - YAML + env config loader (Pydantic v2)
  - CLI with subcommands; logging baseline
  - Tooling: ruff, black, mypy, pytest, pre-commit, CI
  - Basic tests for config/registry/models

- Notes in code:
  - Config: `trading/config/settings.py`
  - Logging helper: `trading/observability/logging.py`
  - CLI entry: `trading/cli.py`

### Phase 2 — Backtester MVP (+ Hardening)
- DONE (backtester core):
  - Data adapters for Parquet cache; fixtures auto-download option
  - Corporate actions: split adjuster
  - Portfolio accounting, costs (slippage bps, fixed commission)
  - Execution simulator (market/limit, participation cap)
  - Risk manager (per-symbol cap, gross exposure, daily loss cap, session gate off in tests)
  - Backtest engine: deterministic bar-close loop, ledgers and metrics, HTML report
  - Observability: counters and timers; `summary.json` with metrics and observability fields

- DONE (Phase 2 hardening polish):
  - K-way timestamp merge for bar alignment in `trading/backtest/engine.py`
  - Deterministic clock injection used in engine (`trading/util/clock.py`)
  - Bars/sec and missing-bars counters recorded in `summary.json`
  - Additional metrics: turnover notional, time-in-market ratio, peak gross exposure

- DONE (Phase 2 validation additions):
  - Property-based tests (portfolio invariants; simulator edge cases)
  - Benchmark target: `make bench-backtest` with SLA (< 60s SPY/QQQ daily)

- Code highlights:
  - Engine: `trading/backtest/engine.py`
  - Metrics: `trading/backtest/metrics.py`
  - Reporting: `trading/reporting/report.py` + `report.html.j2`
  - Risk: `trading/risk/manager.py`
  - Execution: `trading/execution/simulator.py`

### Phase 3 — Live Data & Paper Account Integration
- DONE / IN PROGRESS:
  - Connectivity manager wired via CLI dry-run: `trading/cli.py` (`trade live --dry-run`)
  - Connection hardening: jittered exponential backoff, timeout, and structured logs in `trading/live/connection.py`

- NOT DONE (major items):
  - Market data stream and bar aggregation aligned with backtester
  - Broker adapter for submitting/canceling orders (paper), idempotent ID mapping
  - Reconciliation on reconnect (open orders/positions)
  - Persistence of live orders/fills/positions to SQLite/Parquet
  - Full live CLI loop (non-dry-run), heartbeats during live session
  - Integration tests for live flow (dry-run, forced reconnect), logging shape tests

- Planned but not implemented DB:
  - SQLite is planned (docs) for live snapshots; no DB layer present yet in code

### Phase 3 — Beginner task list (small, explicit steps)
Create these modules and minimal tests. Each step should include a small PR.

1) Persistence (SQLite) skeleton
   - Files: `trading/live/persistence.py`, tests under `tests/live/test_persistence.py`
   - Implement tables for `orders`, `fills`, `positions` (use `sqlite3` or SQLAlchemy)
   - Functions: `init_db(path)`, `upsert_order(...)`, `record_fill(...)`, `snapshot_positions(...)`, `read_open_orders()`

2) Broker adapter (paper) interface + stub
   - Files: `trading/live/broker.py`, tests under `tests/live/test_broker_stub.py`
   - Interface: `BrokerAdapter` with `submit(order)`, `cancel(order_id)`, `open_orders()`, `positions()`; implement idempotent local↔broker ID map

3) Market data stream abstraction
   - Files: `trading/live/market_data.py`, tests under `tests/live/test_market_data.py`
   - For MVP, simulate bars from cached Parquet or poll IBKR with `reqHistoricalData(keepUpToDate)`; output backtester‑aligned bars

4) Live orchestrator skeleton with heartbeats
   - Files: `trading/live/orchestrator.py`, tests under `tests/live/test_live_orchestrator.py`
   - Loop: subscribe → on bar → strategy → risk → broker submit → persist → heartbeat every 60s → on disconnect: backoff + reconnect + resubscribe
   - Wire via CLI: `trading/cli.py` (`trade live --config ...` non‑dry‑run)

5) Reconnect/reconciliation tests (mocked ib_insync)
   - Add tests to simulate disconnect for 15–30s → verify reconnect within ≤ 30s; re‑subscribe; reconcile open orders/positions; no duplication

6) Logging shape tests (JSON mode)
   - Verify fields: `run_id`, `symbols`, `interval`, heartbeats count, reconnect logs present

### What needs to be checked (next validation steps)
- Development hygiene
  - `make ci` passes locally (lint, format, mypy, tests, coverage ≥ 80%)
  - Pre-commit hooks run on commit (Python + Markdown)
- Backtester outputs
  - `trade backtest --config config.example.yaml` produces artifacts under `runs/<run_id>/`
  - `summary.json` contains metrics and observability fields; HTML report renders
- Phase 3 readiness (paper)
  - IB TWS/Gateway configured as per `PHASE3_RUNBOOK.md`; env values set (`TRADE__DATA__IB_HOST|PORT|CLIENT_ID`)
  - Dry-run connectivity works end-to-end; retry/backoff logs emitted
  - Induced disconnect during dry-run shows retry attempts and successful reconnect within target time
  - Decide persistence path (SQLite schema) and add basic write/read test
  - Live orchestrator heartbeat cadence observed in logs (e.g., 60s) with counters increasing

### Problems encountered and how they were solved
- Pre-commit hook failing (WSL) due to Windows venv path baked in
  - Action: reinstalled hooks in WSL venv; added Markdown hooks (`mdformat`, `codespell`); hooks now pass and format docs automatically
- Mypy failures in WSL from scanning `venv_wsl/` and Pydantic typing quirks
  - Action: excluded `venv_wsl/` in `pyproject.toml`; added precise typing in `trading/config/settings.py` (`cast(...)`, cleaned fallbacks); installed `types-PyYAML`; now `python -m mypy .` reports success
- Git push authentication failures and wrong remote owner
  - Action: fixed remote URL; switched to PAT/SSH flow; push to `main` now succeeds
- Live connectivity robustness
  - Action: implemented retry with jittered exponential backoff (`tenacity.wait_random_exponential`), 10s timeout around `connectAsync`, and structured logs for attempt/failure/success in `trading/live/connection.py`

### Dependency management decisions (current)
- Plotly export stability on WSL2
  - Problem: Interactive HTML sometimes hung when loading plotly.js from CDN; Kaleido static export failed/hung under virtualenv paths with spaces (e.g., `/mnt/d/Investment Codes/...`).
  - Actions:
    - Changed HTML embedding to `include_plotlyjs="inline"` to remove network/CDN dependency.
    - Pinned Plotly to `5.18.0` and Kaleido to `0.2.1` in both `pyproject.toml` and `requirements.txt` for known-stable behavior on WSL2.
    - Verified Kaleido PNG export works from a venv located outside spaced paths (`~/.venvs/tradingapp`).
  - Rationale: Avoid CDN hangs; Kaleido wrapper has path-quoting issues with spaces; the pinned versions are stable and sufficient for current reporting needs.

- Single-environment policy and repo hygiene
  - Consolidated to one Ubuntu/WSL virtualenv at `~/.venvs/tradingapp`.
  - Removed legacy local venvs and archived unused helper files.
  - Added `.gitignore` entries for `.hypothesis/` and `Makefile.backup`.

- Strict no-upgrade policy (owner directive)
  - Owner requirement: Do not upgrade packages under any circumstances without explicit approval.
  - Implementation: Pinned versions for Plotly/Kaleido; no automated upgrade tooling suggested or configured. Future work will respect this policy and refrain from proposing or performing dependency version upgrades.

### Known gaps / problems not yet solved
- Live trading core (market data stream, order submission/cancel, reconciliation) is not implemented
- Live persistence layer (SQLite schemas, write/read cycle) is not implemented
- Property-based tests and backtest benchmark target remain open
- Acceptance/integration tests for Phase 3 live flow and reconnect behavior are pending

### Suggested near-term plan
- Implement minimal SQLite persistence module (orders, fills, positions) and wire to live loop scaffolding
- Add broker adapter interfaces and stub implementations (paper) with idempotent ID mapping
- Implement live loop skeleton with heartbeat logging; add reconnect test using mocks
- Add property-based tests and benchmark target for Phase 2 closure

### Glossary (for newcomers)
- Bar: OHLCV record for a fixed interval ending at `end` (UTC)
- Backtester: Deterministic engine that replays historical bars to evaluate strategies
- Heartbeat: Periodic log indicating liveness with counters
- Reconciliation: On reconnect, align local state with broker (open orders, positions)
