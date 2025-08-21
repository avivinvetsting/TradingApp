PY=python
PIP=pip

.PHONY: setup bootstrap dev test lint type fmt precommit backtest live report bench-backtest prune-runs ci

setup:
	$(PY) -m pip install --upgrade pip
	$(PIP) install -e .[dev]

bootstrap:
	bash scripts/setup_env.sh

precommit:
	pre-commit install

lint:
	ruff check .
	black --check .

type:
	mypy .

fmt:
	black .
	ruff check . --fix

test:
	pytest -q

smoke:
	$(PY) -m trading backtest --config config.example.yaml --run-id smoke --heartbeat-every 100000 --no-autodownload || true
	@echo "Report: runs/smoke/reports/report.html"

backtest:
	$(PY) -m trading backtest --config config.example.yaml --run-id $$(date +%Y%m%d-%H%M%S)

live:
	$(PY) -m trading live --config config.example.yaml --dry-run

report:
	@test -n "$(RUN)" || (echo "Usage: make report RUN=<run_id>" && exit 1)
	$(PY) -c "from trading.reporting.report import generate_html_report; print(generate_html_report('runs/$(RUN)'))"

prune-runs:
	$(PY) -m trading ops prune runs --keep-days 30 --apply

ci:
	ruff check . && black --check . && mypy . && pytest --cov=trading --cov-report=term-missing --cov-fail-under=80

bench-backtest:
	$(PY) scripts/bench_backtest.py

open-latest-report:
	@latest=$$(ls -td runs/*/ 2>/dev/null | head -n1); \
	if [ -n "$$latest" ] && [ -f "$$latest/reports/report.html" ]; then \
	  echo "Opening $$latest/reports/report.html"; \
	  explorer.exe "$$(wslpath -w "$$latest/reports/report.html")" 2>/dev/null || true; \
	  echo "Path: $$latest/reports/report.html"; \
	else \
	  echo "No reports found under runs/"; \
	fi
