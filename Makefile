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
