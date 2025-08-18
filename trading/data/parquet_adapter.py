from __future__ import annotations
from pathlib import Path
from typing import Optional

import pandas as pd

from trading.core.contracts import DataAdapter
from trading.core.models import Bar


_TIMEFRAME_MAP = {
    "1D": "1d",
    "1d": "1d",
    "1m": "1m",
    "1h": "1h",
    "60m": "1h",
}


class ParquetLatestBarAdapter(DataAdapter):
    """Reads latest completed bar for a symbol from a Parquet cache.

    Expected file layout: {base_dir}/{symbol}_{interval}.parquet where interval in {1d,1h,1m}.
    Columns required: symbol, end (UTC), open, high, low, close, volume
    """

    def __init__(self, base_dir: str | Path = "data/cache/yf") -> None:
        self.base_dir = Path(base_dir)

    def latest_completed_bar(self, symbol: str, timeframe: str) -> Optional[Bar]:
        interval = _TIMEFRAME_MAP.get(timeframe, timeframe)
        file_path = self.base_dir / f"{symbol}_{interval}.parquet"
        if not file_path.exists():
            return None

        df = pd.read_parquet(file_path)
        if df.empty:
            return None

        # Ensure correct dtypes
        if "end" not in df.columns:
            return None
        if df["end"].dtype != "datetime64[ns, UTC]":
            df["end"] = pd.to_datetime(df["end"], utc=True)

        # Pick the last completed bar by timestamp
        last = df.sort_values("end").iloc[-1]
        return Bar(
            symbol=str(last["symbol"]),
            end=pd.to_datetime(last["end"]).to_pydatetime(),
            open=float(last["open"]),
            high=float(last["high"]),
            low=float(last["low"]),
            close=float(last["close"]),
            volume=int(last["volume"]),
        )
