from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone

from trading.core.contracts import ExecutionEngine
from trading.core.models import Order, Fill


@dataclass
class FillPolicy:
    participation_cap: Optional[float] = None  # 0..1 fraction of volume to allow per bar


class SimpleExecutionSimulator(ExecutionEngine):
    """Deterministic, bar-close execution simulator for market and limit orders.

    - Market: fills entire quantity at bar close price + slippage (bps)
    - Limit: fills if favorable to order side given bar's tradeable range (here: assume close is representative)
    - Optional participation cap limits fill size per bar.
    """

    def __init__(self, slippage_bps: int = 0, fill_policy: Optional[FillPolicy] = None) -> None:
        self.slippage_bps = slippage_bps
        self.fill_policy = fill_policy or FillPolicy()

    def _apply_slippage(self, price: float, side: str) -> float:
        if self.slippage_bps <= 0:
            return price
        bps = self.slippage_bps / 10000.0
        return price * (1 + bps) if side == "buy" else price * (1 - bps)

    def submit(self, order: Order) -> None:  # pragma: no cover - submit delegated via simulate_fill
        return None

    def simulate_fill(
        self,
        *,
        order: Order,
        bar_close: float,
        bar_high: float,
        bar_low: float,
        bar_volume: int,
        fill_ts: Optional[datetime] = None,
    ) -> Optional[Fill]:
        # Determine executable price
        if order.type == "market":
            exec_price = self._apply_slippage(bar_close, order.side)
            qty = order.quantity
        elif order.type == "limit":
            # Buy limit fills if limit >= close (i.e., price moved to our limit or better)
            if order.side == "buy":
                if order.limit_price is None or bar_low > order.limit_price:
                    return None
                exec_price = min(bar_close, order.limit_price)
            else:
                # Sell limit fills if limit <= close
                if order.limit_price is None or bar_high < order.limit_price:
                    return None
                exec_price = max(bar_close, order.limit_price)
            exec_price = self._apply_slippage(exec_price, order.side)
            qty = order.quantity
        else:
            return None

        # Apply participation cap if configured (zero volume or zero cap => no fill)
        if self.fill_policy.participation_cap is not None:
            max_qty = int(bar_volume * self.fill_policy.participation_cap)
            if max_qty <= 0:
                return None
            qty = min(qty, max_qty)
            if qty <= 0:
                return None

        return Fill(
            order_local_id=order.local_id,
            ts=fill_ts or datetime.now(timezone.utc),
            qty=qty,
            price=exec_price,
            commission=0.0,
        )
