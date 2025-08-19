# Phase 3 Runbook — IB Gateway/TWS (Paper)

## Prereqs

- IBKR paper credentials
- Installed TWS or IB Gateway (latest stable)
- Network: ports open to 127.0.0.1:7497 (TWS paper default)

## TWS/Gateway Settings

- Enable API: Configure > API > Settings
  - [x] Enable ActiveX and Socket Clients
  - [x] Read-Only API OFF (allow orders in paper)
  - [x] Trusted IPs: 127.0.0.1
  - Socket port: 7497 (paper)

## Environment

Create `.env` from `.env.example` and set values:

```
TRADE__DATA__IB_HOST=127.0.0.1
TRADE__DATA__IB_PORT=7497
TRADE__DATA__IB_CLIENT_ID=999
```

## Start/Stop

1. Start TWS/Gateway (paper). Confirm API settings.
1. Dry-run connectivity:

```
python -m trading live --config config.example.yaml --dry-run
```

3. Backtest as control:

```
python -m trading backtest --config config.example.yaml --run-id <id>
```

4. Stop: exit TWS/Gateway cleanly.

## Recovery

- If disconnected, the connection manager retries with backoff.
- On reconnect, resubscribe to data and reconcile open orders/positions.

## Checks

- Logs show heartbeats and reconnect attempts.
- No errors about API disabled or port blocked.

## Notes

- Paper account permissions may limit data; delayed data acceptable for development.
