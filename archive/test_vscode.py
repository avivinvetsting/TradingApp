#!/usr/bin/env python3
"""
Test file for VS Code Python 3.11 virtual environment
"""

import sys
import os


def main() -> None:
    print("=== VS Code Python Environment Test ===")
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Virtual Environment: {os.environ.get('VIRTUAL_ENV', 'Not activated')}")

    # Check if we're in the right virtual environment
    if "venv_py311" in sys.executable:
        print("✓ VS Code is using Python 3.11 virtual environment!")
    else:
        print("✗ VS Code is NOT using the Python 3.11 virtual environment")

    # Test imports
    try:
        import pandas as pd

        print(f"✓ Pandas: {pd.__version__}")
    except ImportError:
        print("✗ Pandas not available")

    try:
        import numpy as np

        print(f"✓ NumPy: {np.__version__}")
    except ImportError:
        print("✗ NumPy not available")

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    main()
