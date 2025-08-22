param(
    [switch]$NoDev
)

$ErrorActionPreference = "Stop"

# Resolve project root as parent of this script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
Set-Location $Root

Write-Host "[1/5] Ensuring Python 3.11 is available (py launcher)" -ForegroundColor Cyan
& py -3.11 --version | Write-Host

$VenvPath = Join-Path $Root ".venv"
if (!(Test-Path $VenvPath)) {
    Write-Host "[2/5] Creating virtual environment at $VenvPath" -ForegroundColor Cyan
    & py -3.11 -m venv $VenvPath
} else {
    Write-Host "[2/5] Virtual environment already exists: $VenvPath" -ForegroundColor Yellow
}

Write-Host "[3/5] Activating virtual environment" -ForegroundColor Cyan
& (Join-Path $VenvPath "Scripts/Activate.ps1")

Write-Host "[4/5] Upgrading pip/setuptools/wheel" -ForegroundColor Cyan
python -m pip install -U pip setuptools wheel

Write-Host "[4/5] Installing project requirements" -ForegroundColor Cyan
pip install -r requirements.txt

if (-not $NoDev) {
    Write-Host "[4/5] Installing package in editable mode with dev extras" -ForegroundColor Cyan
    pip install -e .[dev]
} else {
    Write-Host "[4/5] Installing package in editable mode (no dev)" -ForegroundColor Cyan
    pip install -e .
}

# Ensure Windows config exists, create from example if missing
$WinCfg = Join-Path $Root "config.windows.yaml"
if (!(Test-Path $WinCfg)) {
    Write-Host "[4/5] Creating config.windows.yaml from example" -ForegroundColor Cyan
    Copy-Item (Join-Path $Root "config.example.yaml") $WinCfg
    # Best-effort text replacements for localhost defaults
    (Get-Content $WinCfg) `
      -replace 'ib_host:\s*"[^"]+"', 'ib_host: "127.0.0.1"' `
      -replace 'ib_port:\s*\d+', 'ib_port: 4002' `
      | Set-Content $WinCfg -Encoding UTF8
}

Write-Host "[5/5] Running IB connectivity dry-run (Gateway paper: 127.0.0.1:4002)" -ForegroundColor Cyan
python -m trading live --config "$WinCfg" --dry-run --json-logs
