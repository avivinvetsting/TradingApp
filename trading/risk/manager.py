from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional
import pandas as pd

import pandas_market_calendars as mcal

from trading.core.contracts import RiskManager
import logging
from trading.core.models import Order


@dataclass
class RiskParams:
    max_gross_exposure: float
    per_symbol_notional_cap: float
    market_calendar: str = "XNYS"
    daily_loss_cap: Optional[float] = None


class BasicRiskManager(RiskManager):
    """Risk checks: hours gate, per-symbol notional cap, gross exposure cap, daily loss cap.

    Gross exposure and daily loss are provided via callables to avoid tight coupling.
    """

    def __init__(
        self,
        params: RiskParams,
        *,
        get_gross_exposure: Optional[Callable[[], float]] = None,
        get_daily_realized_pnl: Optional[Callable[[], float]] = None,
        enable_session_gate: bool = True,
    ) -> None:
        self.params = params
        self._get_gross_exposure = get_gross_exposure
        self._get_daily_realized_pnl = get_daily_realized_pnl
        self._calendar = mcal.get_calendar(params.market_calendar)
        # In backtests and unit tests, wall-clock session gating should be disabled
        self._enable_session_gate = enable_session_gate

    def validate(self, proposed_order: Order) -> Optional[Order]:
        now = datetime.now(timezone.utc)
        if self._enable_session_gate and not self._is_session_open(now):
            return None

        # Per-symbol notional cap (limit orders)
        notional = 0.0
        if proposed_order.type == "limit" and proposed_order.limit_price is not None:
            notional = proposed_order.limit_price * proposed_order.quantity
            if (
                self.params.per_symbol_notional_cap
                and notional > self.params.per_symbol_notional_cap
            ):
                return None

        # Daily loss cap
        if self.params.daily_loss_cap is not None and self._get_daily_realized_pnl is not None:
            try:
                daily_realized = float(self._get_daily_realized_pnl())
                if daily_realized < -abs(self.params.daily_loss_cap):
                    return None
            except Exception as exc:
                logging.getLogger(__name__).warning(
                    "daily loss cap check failed; allowing order",
                    extra={"error": str(exc)},
                )

        # Gross exposure cap
        if self.params.max_gross_exposure and self._get_gross_exposure is not None and notional > 0:
            try:
                gross = float(self._get_gross_exposure())
                if gross + abs(notional) > self.params.max_gross_exposure:
                    return None
            except Exception as exc:
                logging.getLogger(__name__).warning(
                    "gross exposure check failed; allowing order",
                    extra={"error": str(exc)},
                )

        return proposed_order

    def _is_session_open(self, now: datetime) -> bool:
        day = pd.Timestamp(now).tz_convert("UTC").normalize()
        sched = self._calendar.schedule(start_date=day.date(), end_date=day.date())
        if sched.empty:
            return False
        market_open = sched.iloc[0]["market_open"].tz_convert("UTC")
        market_close = sched.iloc[0]["market_close"].tz_convert("UTC")
        return market_open <= pd.Timestamp(now) <= market_close
