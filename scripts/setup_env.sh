#!/usr/bin/env bash
set -euo pipefail

# Setup a single Python 3.11 virtual environment on WSL Ubuntu and install all dependencies
# - Creates .venv
# - Installs requirements and the package in editable mode
# - Installs pre-commit hooks and a Jupyter kernel
# - Verifies Plotly export and runs tests

REPO_ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$REPO_ROOT_DIR"

echo "[1/7] Verifying WSL/Ubuntu environment"
if ! grep -qi microsoft /proc/version 2>/dev/null; then
  echo "This script is intended for WSL. Continuing anyway..." >&2
fi

# Choose Python 3.11 if available
PY_BIN="python3.11"
if ! command -v "$PY_BIN" >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    PY_BIN="python3"
  else
    PY_BIN="python"
  fi
fi

echo "Using Python: $($PY_BIN -V)"

VENV_DIR=".venv"

echo "[2/7] Creating fresh virtual environment at $VENV_DIR"
# Remove old/extra envs if present
rm -rf .venv_win 2>/dev/null || true
rm -rf venv_py311 2>/dev/null || true
rm -rf venv_wsl 2>/dev/null || true
# Recreate .venv
rm -rf "$VENV_DIR"
"$PY_BIN" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "[3/7] Upgrading pip/setuptools/wheel"
python -m pip install -U pip setuptools wheel

echo "[4/7] Installing project requirements and package (editable)"
pip install -r requirements.txt
pip install -e .

echo "[5/7] Installing dev tooling hooks and Jupyter kernel"
pre-commit install || true
python -m ipykernel install --user --name TradingApp --display-name "Python (TradingApp)" || true

echo "[6/7] Verifying Plotly static export (Kaleido)"
python scripts/verify_plotly.py || true

echo "[7/7] Running test suite"
pytest -q || true

ACTIVATE_HINT="source $VENV_DIR/bin/activate"

echo
echo "Done. To start using the environment in new shells, run:"
echo "  $ACTIVATE_HINT"
echo
echo "In VS Code, select interpreter: $REPO_ROOT_DIR/$VENV_DIR/bin/python"
