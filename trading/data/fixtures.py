from __future__ import annotations
from pathlib import Path
from typing import Iterable

import pandas as pd
import yfinance as yf


def download_yf_bars(
    symbols: Iterable[str],
    interval: str = "1d",
    start: str | None = None,
    end: str | None = None,
    out_dir: str | Path = "data/cache/yf",
) -> list[Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        df = ticker.history(interval=interval, start=start, end=end, auto_adjust=False)
        if df.empty:
            continue
        df = df.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        df.index.name = "end"
        df.reset_index(inplace=True)
        df.insert(0, "symbol", symbol)
        # Ensure UTC timestamp
        if not pd.api.types.is_datetime64_any_dtype(df["end"]):
            df["end"] = pd.to_datetime(df["end"], utc=True)
        else:
            df["end"] = (
                df["end"].dt.tz_convert("UTC")
                if df["end"].dt.tz is not None
                else df["end"].dt.tz_localize("UTC")
            )

        out_path = out / f"{symbol}_{interval}.parquet"
        df[["symbol", "end", "open", "high", "low", "close", "volume"]].to_parquet(
            out_path, index=False
        )
        saved.append(out_path)

    return saved
