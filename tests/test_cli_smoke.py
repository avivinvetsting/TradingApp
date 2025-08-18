from __future__ import annotations
from pathlib import Path
import os
import subprocess
import sys
import pandas as pd


def test_backtest_smoke_uses_tmp_cache(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Prepare minimal parquet files for SPY and QQQ expected by config.example.yaml
    rows = [
        {
            "symbol": "SPY",
            "end": "2024-01-02T21:00:00Z",
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1000,
        }
    ]
    pd.DataFrame(rows).to_parquet(cache_dir / "SPY_1d.parquet", index=False)
    rows[0]["symbol"] = "QQQ"
    pd.DataFrame(rows).to_parquet(cache_dir / "QQQ_1d.parquet", index=False)

    env = os.environ.copy()
    env["TRADE__DATA__CACHE_DIR"] = str(cache_dir)

    cmd = [
        sys.executable,
        "-m",
        "trading",
        "backtest",
        "--config",
        "config.example.yaml",
        "--run-id",
        "smoke-test",
        "--out-dir",
        str(tmp_path / "runs"),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root, env=env)
    assert proc.returncode == 0, proc.stderr
    run_dir = tmp_path / "runs" / "smoke-test"
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "equity.parquet").exists()
