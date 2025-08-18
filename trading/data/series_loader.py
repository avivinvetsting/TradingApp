from __future__ import annotations
from pathlib import Path
import pandas as pd


def load_parquet_series(base_dir: str | Path, symbol: str, interval: str) -> pd.DataFrame:
    """Load a historical bar series for a symbol/interval from a Parquet file.

    Expects columns: symbol, end (UTC), open, high, low, close, volume
    Returns DataFrame sorted by end ascending with UTC timestamps.
    """
    path = Path(base_dir) / f"{symbol}_{interval}.parquet"
    df = pd.read_parquet(path)
    df["end"] = pd.to_datetime(df["end"], utc=True)
    df = df.sort_values("end").reset_index(drop=True)
    return df[["symbol", "end", "open", "high", "low", "close", "volume"]]
