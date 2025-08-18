from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from typing import Dict

import pandas as pd


_INTERVAL_TO_PPY: Dict[str, int] = {
    "1d": 252,
    "1h": int(252 * 6.5),  # trading hours per day
    "1m": 252 * 390,  # minutes per trading day
}


@dataclass
class Metrics:
    cagr: float
    sharpe: float
    sortino: float
    max_drawdown: float
    calmar: float
    hit_rate: float


def compute_from_equity(equity_df: pd.DataFrame, interval: str) -> Metrics:
    df = equity_df.copy()
    df = df.sort_values("ts")
    start_equity = float(df["equity"].iloc[0])
    end_equity = float(df["equity"].iloc[-1])
    n = len(df)
    ppy = _INTERVAL_TO_PPY.get(interval, 252)

    # Simple returns from equity
    returns = df["equity"].pct_change().dropna()
    mean_r = float(returns.mean()) if not returns.empty else 0.0
    std_r = float(returns.std(ddof=1)) if len(returns) > 1 else 0.0
    downside = returns[returns < 0.0]
    std_down = float(downside.std(ddof=1)) if len(downside) > 1 else 0.0

    # CAGR
    cagr = (end_equity / start_equity) ** (ppy / max(1, n)) - 1.0 if n > 1 else 0.0

    # Sharpe and Sortino (risk-free assumed 0)
    sharpe = (mean_r * sqrt(ppy) / std_r) if std_r > 0 else 0.0
    sortino = (mean_r * sqrt(ppy) / std_down) if std_down > 0 else 0.0

    # Max drawdown and Calmar
    roll_max = df["equity"].cummax()
    drawdowns = df["equity"] / roll_max - 1.0
    max_dd = float(drawdowns.min()) if not drawdowns.empty else 0.0
    calmar = (cagr / abs(max_dd)) if max_dd < 0 else 0.0

    # Hit rate
    hit_rate = float((returns > 0).mean()) if not returns.empty else 0.0

    return Metrics(
        cagr=cagr,
        sharpe=sharpe,
        sortino=sortino,
        max_drawdown=max_dd,
        calmar=calmar,
        hit_rate=hit_rate,
    )
