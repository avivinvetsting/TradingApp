# TradingApp

Algorithmic trading bot scaffold (IBKR, Python 3.11). See `PROJECT_PLAN.md` and `DETAILED_PHASE_PLAN.md` for scope and milestones.

Quick start

- Create/activate Python 3.11 venv
- Install
  ```bash
  pip install -e .[dev]
  pre-commit install
  ```
- Verify
  ```bash
  ruff check . && black --check . && mypy . && pytest -q
  python -m trading --help
  ```

Development

- One-shot CI locally
  ```bash
  make ci
  ```
- Install pre-commit hooks (recommended)
  ```bash
  make precommit
  pre-commit run --all-files
  ```

Phase 3 Runbook

See `PHASE3_RUNBOOK.md` for TWS/Gateway settings, env vars, and start/stop/recovery steps.

Run a backtest (auto-downloads cache if missing)
```bash
python -m trading backtest --config config.example.yaml --run-id test-run
# Artifacts in runs/test-run/: equity.parquet, orders.parquet, fills.parquet, summary.json (with metrics)
```

Utilities

- Manual fixtures from yfinance (optional; backtest auto-downloads if needed)
  ```bash
  python -m trading fixtures download SPY QQQ --interval 1d --start 2024-01-01 --out-dir data/cache
  ```
- Prune artifacts
  ```bash
  python -m trading ops prune runs --keep-days 14
  ```
