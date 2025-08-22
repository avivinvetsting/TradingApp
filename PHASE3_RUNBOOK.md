# Phase 3 Runbook — IBKR TWS/IB Gateway Connectivity (Exact Steps)

This checklist is the single source of truth for establishing a reliable connection to IBKR via TWS/IB Gateway. It is optimized for Windows PowerShell (native) and includes WSL2 notes. Follow it in order to avoid port/venv issues.

## 1) Prerequisites

- IBKR account (Paper or Live)
- Installed TWS (recommended) or IB Gateway (latest stable)
- Python 3.11 installed on Windows
- Project cloned locally (path without restrictions)

## 2) TWS/IB Gateway API settings

In TWS: File → Global Configuration → API → Settings
- Enable ActiveX and Socket Clients: ON
- Read-Only API: OFF (allow orders for paper; keep careful in live)
- Allow connections from localhost: ON
- Trusted IPs: include 127.0.0.1
- Socket port:
  - TWS Live: 7496
  - TWS Paper: 7497 (recommended for dev)
  - IBG Live: 4001; IBG Paper: 4002
Click OK and restart TWS after changes.

Verify listener (PowerShell):
```powershell
netstat -ano | findstr /R /C:":7496 " /C:":7497 " /C:":4001 " /C:":4002 "
```
If nothing shows, TWS/IBG isn’t listening. Recheck settings, apply, and restart.

## 3) Windows venv and install (PowerShell)

From the repo root (e.g., `D:\Investment Codes\TradingApp`):
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel
pip install -e .[dev]
```
Sanity check:
```powershell
python -m trading --help
```
If you see “No pyvenv.cfg file”, install a standard Python from python.org, recreate the venv, and ensure `where python` points to `.venv\\Scripts\\python.exe`.

## 4) Configuration (Windows)

Use the provided Windows config preset that matches TWS Paper by default:
- `config.windows.yaml` contains:
  - `data.ib_host: 127.0.0.1`
  - `data.ib_port: 7497`
  - `data.ib_client_id: 1`

You can override at runtime without editing files via environment variables:
```powershell
$env:TRADE__DATA__IB_HOST="127.0.0.1"
$env:TRADE__DATA__IB_PORT="7497"   # 7496 for Live TWS
$env:TRADE__DATA__IB_CLIENT_ID="1"
```

## 5) Dry-run connectivity test (no orders)

Run from repo root (PowerShell):
```powershell
python -m trading live --config "config.windows.yaml" --dry-run --json-logs --log-level DEBUG
```
Expected logs:
- `connect_attempt` → `connect_success` → `ib_connected` → `ib_disconnected`

If connection is refused, confirm the open port with `netstat` and ensure TWS is configured to that port and restarted.

## 6) Known-good sanity scripts (fallback)

If you need to validate TWS independently, use the archived working samples:
```powershell
python .\archive\IBKR_api\test_tws_connection.py         # verifies connection + prints quotes
python .\archive\IBKR_api\check_account_type.py          # confirms account info/type
```
Defaults target `127.0.0.1:7496` (Live). For Paper, change the port to `7497` inside those scripts or set the TWS socket to 7497.

## 7) WSL2 notes (optional)

If running from WSL instead of Windows PowerShell:
- Host (Windows) IP from WSL: check `cat /etc/resolv.conf` or `ip route | awk '/default/ {print $3}'` (often `172.22.0.1`).
- Set YAML or env to `ib_host=<windows_ip>` and port as above.
- Add your WSL IP to TWS Trusted IPs (`hostname -I | awk '{print $1}'`).

## 8) Troubleshooting (by symptom)

- Connection refused / timeout:
  - TWS/IBG not running or wrong port; verify with `netstat`.
  - API not enabled; restart after enabling.
  - “Allow localhost only” ON but connecting from WSL: either disable or add WSL IP to Trusted IPs.
- Client ID already in use:
  - Use a different `ib_client_id` (e.g., 2, 3, 100) in env or YAML.
- Pop-up in TWS for API access:
  - Accept the connection; optionally enable auto-accept in API settings.
- `ib_insync` not found:
  - Ensure you installed in the active venv: `pip install -e .[dev]`.
- “No pyvenv.cfg file”:
  - You’re using a minimal Python; install full Python 3.11, recreate venv.

## 9) Live vs Paper quick switch

- Paper (recommended for dev): set socket to 7497 in TWS; ensure YAML/env `IB_PORT=7497`.
- Live: set socket to 7496; ensure YAML/env `IB_PORT=7496`. Consider changing `ib_client_id` to avoid collisions with other tools.

## 10) Backtest control (optional)

Run a backtest to validate environment and reporting:
```powershell
python -m trading backtest --config config.example.yaml --run-id test-run
```

## 11) Recovery

- The connection manager uses exponential backoff with jitter and retries on failure.
- On reconnect, the live loop (when implemented) must resubscribe to data and reconcile open orders/positions.

## 12) Expected baseline

- A successful dry-run shows `connect_success` and clean disconnect within a second or two.
- For Windows, `config.windows.yaml` + TWS Paper (7497) is the default, verified setup.
