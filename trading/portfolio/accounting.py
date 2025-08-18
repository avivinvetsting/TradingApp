from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

from trading.core.models import Fill, PortfolioSnapshot, Position


@dataclass
class PortfolioState:
    """In-memory portfolio accounting with cash, positions, and realized PnL.

    Prices are assumed in account currency. Commission is accounted as cash outflow
    and reduces realized PnL when associated to a sell.
    """

    cash: float
    positions: Dict[str, Position] = field(default_factory=dict)
    realized_pnl: float = 0.0

    def get_position(self, symbol: str) -> Position:
        pos = self.positions.get(symbol)
        if pos is None:
            pos = Position(symbol=symbol, qty=0, avg_price=0.0)
            self.positions[symbol] = pos
        return pos

    def apply_fill(self, fill: Fill, price: float, symbol: str, commission: float) -> None:
        """Apply a fill to the portfolio.

        - For buys: increase quantity, update VWAP avg_price, reduce cash by (qty*price + commission)
        - For sells: decrease quantity, realize PnL: (price - avg_price) * qty - commission, increase cash by (qty*price - commission)
        """
        if fill.qty == 0:
            return
        position = self.get_position(symbol)
        is_buy = fill.qty > 0
        qty = abs(fill.qty)

        if is_buy:
            # New total quantity after buy
            new_qty = position.qty + qty
            # New average price (VWAP of existing and incoming)
            if new_qty == 0:
                position.avg_price = 0.0
            else:
                position.avg_price = (position.avg_price * position.qty + price * qty) / new_qty
            position.qty = new_qty
            # Cash outflow includes commission
            self.cash -= price * qty
            self.cash -= commission
        else:
            # Sell
            if qty > position.qty:
                raise ValueError("Cannot sell more than current position quantity")
            # Realize PnL on sold shares (commission reduces realized PnL)
            pnl = (price - position.avg_price) * qty - commission
            self.realized_pnl += pnl
            # Reduce position quantity; avg_price unchanged for remaining
            position.qty -= qty
            if position.qty == 0:
                position.avg_price = 0.0
            # Cash inflow net of commission
            self.cash += price * qty
            self.cash -= commission

    def snapshot(
        self, as_of: Optional[datetime] = None, marks: Optional[Dict[str, float]] = None
    ) -> PortfolioSnapshot:
        """Create a snapshot with unrealized PnL and equity at given marks.

        - marks: mapping symbol -> last price for mark-to-market. Missing symbols are treated as last avg_price.
        """
        marks = marks or {}
        as_of = as_of or datetime.now(timezone.utc)
        unrealized = 0.0
        equity = self.cash
        for symbol, position in self.positions.items():
            if position.qty == 0:
                continue
            mark = marks.get(symbol, position.avg_price)
            position_value = mark * position.qty
            equity += position_value
            unrealized += (mark - position.avg_price) * position.qty
        return PortfolioSnapshot(
            ts=as_of,
            cash=self.cash,
            equity=equity,
            unrealized_pnl=unrealized,
            realized_pnl=self.realized_pnl,
        )
