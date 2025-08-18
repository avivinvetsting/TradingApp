from __future__ import annotations
from trading.core.models import Order
from trading.execution.simulator import SimpleExecutionSimulator, FillPolicy


def test_market_order_slippage() -> None:
    sim = SimpleExecutionSimulator(slippage_bps=10)
    order = Order(local_id="o1", symbol="SPY", side="buy", type="market", quantity=100)
    fill = sim.simulate_fill(
        order=order, bar_close=100.0, bar_high=101.0, bar_low=99.0, bar_volume=100000
    )
    assert fill is not None
    # 10 bps slippage => price * 1.001 for buy
    assert abs(fill.price - 100.1) < 1e-6


def test_limit_order_buy_and_sell() -> None:
    sim = SimpleExecutionSimulator(slippage_bps=0)
    buy = Order(
        local_id="o2", symbol="SPY", side="buy", type="limit", quantity=10, limit_price=100.0
    )
    sell = Order(
        local_id="o3", symbol="SPY", side="sell", type="limit", quantity=10, limit_price=100.0
    )

    # Close 99 => buy should fill (<= limit)
    fb = sim.simulate_fill(order=buy, bar_close=99.0, bar_high=100.0, bar_low=98.0, bar_volume=1000)
    assert fb is not None

    # Close 101 => sell should fill (>= limit)
    fs = sim.simulate_fill(
        order=sell, bar_close=101.0, bar_high=102.0, bar_low=99.0, bar_volume=1000
    )
    assert fs is not None


def test_participation_cap() -> None:
    sim = SimpleExecutionSimulator(slippage_bps=0, fill_policy=FillPolicy(participation_cap=0.1))
    order = Order(local_id="o4", symbol="SPY", side="buy", type="market", quantity=1000)
    # 10% of 500 volume => max 50 shares
    fill = sim.simulate_fill(
        order=order, bar_close=100.0, bar_high=101.0, bar_low=99.0, bar_volume=500
    )
    assert fill is not None
    assert fill.qty == 50
