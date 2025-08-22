# PowerShell script to activate Python 3.11 virtual environment
Write-Host "Activating Python 3.11 Virtual Environment..." -ForegroundColor Green

# Check if virtual environment exists
if (Test-Path "venv_py311\Scripts\Activate.ps1") {
    Write-Host "Virtual environment found!" -ForegroundColor Yellow

    # Activate the virtual environment
    & "venv_py311\Scripts\Activate.ps1"

    Write-Host "Virtual environment activated!" -ForegroundColor Green
    Write-Host "Python version:" -ForegroundColor Yellow
    python --version

    Write-Host "`nTo deactivate, run: deactivate" -ForegroundColor Cyan
} else {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create it first with: python -m venv venv_py311" -ForegroundColor Red
}
