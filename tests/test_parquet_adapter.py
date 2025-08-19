from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import pytest

from trading.data.parquet_adapter import ParquetLatestBarAdapter
from trading.data.series_loader import load_parquet_series


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


def test_series_loader_raises_on_wrong_dtypes(tmp_path: Path) -> None:
    # Write malformed parquet (end as string, volume as string)
    file = tmp_path / "SPY_1d.parquet"
    rows = [
        {"symbol": "SPY", "end": "2024-01-01T21:00:00Z", "open": 100, "high": 101, "low": 99, "close": 100.5, "volume": "1000"}
    ]
    pd.DataFrame(rows).to_parquet(file, index=False)
    with pytest.raises(Exception):
        load_parquet_series(tmp_path, "SPY", "1d")


def test_adapter_handles_end_as_string(tmp_path: Path) -> None:
    base = tmp_path
    file = base / "QQQ_1d.parquet"
    rows = [
        {
            "symbol": "QQQ",
            "end": "2024-01-03T21:00:00Z",
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1000,
        }
    ]
    _write_parquet(file, rows)
    adapter = ParquetLatestBarAdapter(base_dir=base)
    bar = adapter.latest_completed_bar("QQQ", "1D")
    assert bar is not None
    assert bar.symbol == "QQQ"
    assert bar.end.isoformat().startswith("2024-01-03")


def test_series_loader_rejects_duplicate_timestamps(tmp_path: Path) -> None:
    base = tmp_path
    file = base / "SPY_1d.parquet"
    rows = [
        {"symbol": "SPY", "end": "2024-01-03T21:00:00Z", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000},
        {"symbol": "SPY", "end": "2024-01-03T21:00:00Z", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000},
    ]
    _write_parquet(file, rows)
    with pytest.raises(Exception):
        load_parquet_series(base, "SPY", "1d")
