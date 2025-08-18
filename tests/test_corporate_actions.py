from __future__ import annotations
from datetime import datetime, timezone

import pandas as pd

from trading.data.corporate_actions import SplitEvent, apply_split_adjustments


def test_apply_split_adjustments_simple() -> None:
    bars = pd.DataFrame(
        [
            {
                "end": datetime(2020, 1, 1, tzinfo=timezone.utc),
                "open": 100.0,
                "high": 110.0,
                "low": 90.0,
                "close": 105.0,
                "volume": 1000,
            },
            {
                "end": datetime(2020, 1, 10, tzinfo=timezone.utc),
                "open": 102.0,
                "high": 112.0,
                "low": 92.0,
                "close": 106.0,
                "volume": 1100,
            },
            {
                "end": datetime(2020, 2, 1, tzinfo=timezone.utc),
                "open": 104.0,
                "high": 114.0,
                "low": 94.0,
                "close": 108.0,
                "volume": 1200,
            },
        ]
    )
    splits = [SplitEvent(date=datetime(2020, 1, 15, tzinfo=timezone.utc), ratio=2.0)]

    adj = apply_split_adjustments(bars, splits)

    # Bars before 2020-01-15 should be divided by 2 in price and multiplied by 2 in volume
    assert adj.loc[0, "close"] == 105.0 / 2
    assert adj.loc[1, "close"] == 106.0 / 2
    assert adj.loc[0, "volume"] == 1000 * 2
    assert adj.loc[1, "volume"] == 1100 * 2

    # Bars after split unchanged
    assert adj.loc[2, "close"] == 108.0
    assert adj.loc[2, "volume"] == 1200
