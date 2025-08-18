PY=python
PIP=pip

.PHONY: setup dev test lint type fmt precommit backtest live

setup:
	$(PY) -m pip install --upgrade pip
	$(PIP) install -e .[dev]

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
