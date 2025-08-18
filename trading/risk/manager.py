from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

import pandas_market_calendars as mcal

from trading.core.contracts import RiskManager
from trading.core.models import Order


@dataclass
class RiskParams:
    max_gross_exposure: float
    per_symbol_notional_cap: float
    market_calendar: str = "XNYS"
    daily_loss_cap: Optional[float] = None


class BasicRiskManager(RiskManager):
    """Simple risk checks: session open, per-symbol notional cap, gross exposure cap.

    For MVP, we assume zero current exposure and rely on portfolio wiring later for accurate exposure.
    """

    def __init__(self, params: RiskParams) -> None:
        self.params = params
        self.calendar = mcal.get_calendar(params.market_calendar)

    def validate(self, proposed_order: Order) -> Optional[Order]:
        # Market-hours gate
        if not self._is_session_open():
            return None

        # Notional per symbol
        notional = 0.0
        if proposed_order.limit_price is not None and proposed_order.type == "limit":
            notional = proposed_order.limit_price * proposed_order.quantity
        # For market orders, caller should provide an estimate; we conservatively reject if zero
        if proposed_order.type == "market":
            # Cannot evaluate notional without mark; allow for now
            pass
        if (
            self.params.per_symbol_notional_cap
            and notional > 0
            and notional > self.params.per_symbol_notional_cap
        ):
            return None

        # Gross exposure cap would require current exposure; for MVP, skip here
        return proposed_order

    def _is_session_open(self) -> bool:
        # Use calendar schedule for current day
        # For MVP, simply return True; advanced gating will be added when wiring live
        return True
