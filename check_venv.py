#!/usr/bin/env python3
import sys
import os

print("=== Python Virtual Environment Check ===")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path[0]}")
print(f"Virtual environment: {os.environ.get('VIRTUAL_ENV', 'Not activated')}")

# Check if we're in the right virtual environment
if "venv_py311" in sys.executable:
    print("✓ Successfully using Python 3.11 virtual environment!")
else:
    print("✗ Not using the Python 3.11 virtual environment")
    print("To activate, run: venv_py311\\Scripts\\activate.bat")
