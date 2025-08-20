from __future__ import annotations

import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    run_id = f"bench-{uuid.uuid4().hex[:8]}"
    cmd = [
        sys.executable,
        "-m",
        "trading",
        "backtest",
        "--config",
        str(ROOT / "config.example.yaml"),
        "--run-id",
        run_id,
        "--heartbeat-every",
        "100000",
        "--no-autodownload",
    ]
    print("Command:", " ".join(cmd))
    start = time.perf_counter()
    rc = subprocess.call(cmd)
    elapsed = time.perf_counter() - start
    print(f"elapsed_seconds={elapsed:.3f}")
    if rc != 0:
        return rc
    if elapsed > 60.0:
        print("SLA FAILED: backtest exceeded 60 seconds", file=sys.stderr)
        return 1
    print("SLA OK: backtest within 60 seconds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
