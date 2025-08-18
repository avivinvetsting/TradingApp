from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

from trading.data.parquet_adapter import ParquetLatestBarAdapter


def _write_parquet(path: Path, rows: list[dict[str, object]]) -> None:
    df = pd.DataFrame(rows)
    df.to_parquet(path, index=False)


def test_latest_completed_bar_missing_file(tmp_path: Path) -> None:
    adapter = ParquetLatestBarAdapter(base_dir=tmp_path)
    bar = adapter.latest_completed_bar("SPY", "1D")
    assert bar is None


def test_latest_completed_bar_returns_last_row(tmp_path: Path) -> None:
    base = tmp_path
    file = base / "SPY_1d.parquet"
    rows = [
        {
            "symbol": "SPY",
            "end": datetime(2024, 1, 2, 21, 0, tzinfo=timezone.utc),
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1000,
        },
        {
            "symbol": "SPY",
            "end": datetime(2024, 1, 3, 21, 0, tzinfo=timezone.utc),
            "open": 101.0,
            "high": 102.0,
            "low": 100.0,
            "close": 101.5,
            "volume": 1100,
        },
    ]
    _write_parquet(file, rows)

    adapter = ParquetLatestBarAdapter(base_dir=base)
    bar = adapter.latest_completed_bar("SPY", "1D")
    assert bar is not None
    assert bar.symbol == "SPY"
    assert bar.close == 101.5
    assert bar.end.isoformat().startswith("2024-01-03")
