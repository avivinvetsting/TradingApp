from __future__ import annotations
from typing import Optional

from trading.core.contracts import Strategy
from trading.core.models import Bar, Order
from trading.strategy.registry import register_strategy


@register_strategy("momentum")
class MomentumStrategy(Strategy):
    def __init__(self, lookback: int = 10, symbol: str | None = None) -> None:
        self.lookback = lookback
        self.symbol = symbol

    def on_bar(self, bar: Bar) -> Optional[Order]:
        # Placeholder: returns no orders in stub
        return None
