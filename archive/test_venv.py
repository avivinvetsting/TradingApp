#!/usr/bin/env python3
"""
Test script for Python 3.11 virtual environment
"""

import sys
import platform


def main() -> None:
    print("=== Python 3.11 Virtual Environment Test ===")
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.architecture()}")

    # Check if we're in the virtual environment
    if "venv_py311" in sys.executable:
        print("✓ Successfully using Python 3.11 virtual environment!")
    else:
        print("✗ Not using the Python 3.11 virtual environment")

    # Test basic imports
    try:
        import pandas as pd

        print(f"✓ Pandas imported successfully: {pd.__version__}")
    except ImportError as e:
        print(f"✗ Pandas import failed: {e}")

    try:
        import numpy as np

        print(f"✓ NumPy imported successfully: {np.__version__}")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")

    print("\n=== Environment Test Complete ===")


if __name__ == "__main__":
    main()
