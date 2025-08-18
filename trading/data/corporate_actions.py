from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import List, Sequence

import pandas as pd

try:
    import yfinance as yf  # optional; used only if available
except Exception:  # pragma: no cover
    yf = None


@dataclass(frozen=True)
class SplitEvent:
    """Represents a stock split event.

    ratio: e.g., 2.0 means 2-for-1 (prices halved before the event)
    """

    date: datetime
    ratio: float


def fetch_yf_splits(symbol: str) -> List[SplitEvent]:
    """Fetch split events via yfinance for a symbol.

    Returns a list of SplitEvent sorted by date ascending. If yfinance is not
    available, returns an empty list.
    """
    if yf is None:
        return []
    s = yf.Ticker(symbol).splits
    events: List[SplitEvent] = []
    if s is None or len(s) == 0:
        return events
    for ts, ratio in s.items():
        events.append(
            SplitEvent(date=pd.to_datetime(ts, utc=True).to_pydatetime(), ratio=float(ratio))
        )
    events.sort(key=lambda e: e.date)
    return events


def apply_split_adjustments(bars: pd.DataFrame, splits: Sequence[SplitEvent]) -> pd.DataFrame:
    """Back-adjust prices and volumes for given split events.

    - Prices before a split are divided by the cumulative split ratio
    - Volumes before a split are multiplied by the cumulative split ratio

    bars must include: end (datetime), open, high, low, close, volume
    Returns a new DataFrame with the same columns adjusted.
    """
    if bars.empty or not splits:
        return bars.copy()

    df = bars.copy()
    if "end" not in df.columns:
        raise ValueError("bars must include an 'end' column")

    df["end"] = pd.to_datetime(df["end"], utc=True)
    df = df.sort_values("end").reset_index(drop=True)

    # Build cumulative factors for each bar
    factors = pd.Series(1.0, index=df.index)
    cumulative = 1.0
    for event in sorted(splits, key=lambda e: e.date):
        cumulative *= float(event.ratio)
        mask = df["end"] < pd.to_datetime(event.date, utc=True)
        factors.loc[mask] = cumulative

    # Adjust prices and volume
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col] / factors
    df["volume"] = (df["volume"] * factors).round().astype(int)

    return df
