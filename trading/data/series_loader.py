from __future__ import annotations
from pathlib import Path
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype


def load_parquet_series(base_dir: str | Path, symbol: str, interval: str) -> pd.DataFrame:
    """Load a historical bar series for a symbol/interval from a Parquet file.

    Expects columns: symbol, end (UTC), open, high, low, close, volume
    Returns DataFrame sorted by end ascending with UTC timestamps.
    """
    path = Path(base_dir) / f"{symbol}_{interval}.parquet"
    df = pd.read_parquet(path)
    # Schema validation
    required = ["symbol", "end", "open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Parquet schema invalid for {path}: missing columns {missing}")
    # Coerce dtypes
    if not is_datetime64_any_dtype(df["end"]):
        df["end"] = pd.to_datetime(df["end"], utc=True, errors="coerce")
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").astype("Int64")
    if df[["open", "high", "low", "close", "volume"]].isnull().any().any():
        raise ValueError(f"Parquet data has invalid dtypes or NaNs for {path}")
    df = df.sort_values("end").reset_index(drop=True)
    # Enforce strictly increasing timestamps (no duplicates)
    if df["end"].duplicated().any():
        dupes = df[df["end"].duplicated()]["end"].astype(str).head(3).tolist()
        raise ValueError(
            f"Parquet data has duplicate timestamps for {symbol} {interval}; examples: {dupes}"
        )
    return df[["symbol", "end", "open", "high", "low", "close", "volume"]]
