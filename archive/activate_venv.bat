@echo off
echo Activating Python 3.11 Virtual Environment...
call venv_py311\Scripts\activate.bat
echo.
echo Virtual environment activated!
echo Python version:
venv_py311\Scripts\python.exe --version
echo.
echo To deactivate, run: deactivate
cmd /k
