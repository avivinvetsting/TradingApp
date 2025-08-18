from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from trading.core.contracts import Strategy
from trading.core.models import Bar, Order
from trading.strategy.registry import register_strategy


@dataclass
class MACrossoverState:
    fast: float | None = None
    slow: float | None = None


@register_strategy("ma_crossover")
class MovingAverageCrossover(Strategy):
    def __init__(self, fast: int = 20, slow: int = 50, symbol: str | None = None) -> None:
        self.fast_window = fast
        self.slow_window = slow
        self.symbol = symbol
        self.state = MACrossoverState()

    def on_bar(self, bar: Bar) -> Optional[Order]:
        # Placeholder: no actual MA calculation; returns no orders in stub
        return None
