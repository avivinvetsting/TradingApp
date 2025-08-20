from __future__ import annotations

from hypothesis import given, strategies as st, settings, HealthCheck

from trading.core.models import Order
from trading.execution.simulator import SimpleExecutionSimulator, FillPolicy


@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None, max_examples=100)
@given(
    side=st.sampled_from(["buy", "sell"]),
    slippage_bps=st.integers(min_value=0, max_value=500),
    close=st.floats(min_value=0.01, max_value=10000, allow_nan=False, allow_infinity=False),
)
def test_market_slippage_direction(side: str, slippage_bps: int, close: float) -> None:
    sim = SimpleExecutionSimulator(slippage_bps=slippage_bps)
    order = Order(local_id="o", symbol="SPY", side=side, type="market", quantity=100)
    fill = sim.simulate_fill(
        order=order, bar_close=close, bar_high=close, bar_low=close, bar_volume=1
    )
    assert fill is not None
    if slippage_bps == 0:
        assert abs(fill.price - close) < 1e-9
    else:
        if side == "buy":
            assert fill.price > close
        else:
            assert fill.price < close


@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None, max_examples=100)
@given(
    quantity=st.integers(min_value=1, max_value=1_000_000),
    volume=st.integers(min_value=0, max_value=10_000_000),
    cap=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
def test_participation_cap_limits_quantity(quantity: int, volume: int, cap: float) -> None:
    sim = SimpleExecutionSimulator(slippage_bps=0, fill_policy=FillPolicy(participation_cap=cap))
    order = Order(local_id="o", symbol="SPY", side="buy", type="market", quantity=quantity)
    fill = sim.simulate_fill(
        order=order, bar_close=100.0, bar_high=100.0, bar_low=100.0, bar_volume=volume
    )
    if volume == 0 or int(volume * cap) <= 0:
        assert fill is None
    else:
        assert fill is not None
        assert 0 < fill.qty <= min(quantity, int(volume * cap))


@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None, max_examples=100)
@given(
    limit=st.floats(min_value=0.01, max_value=1000, allow_nan=False, allow_infinity=False),
    low=st.floats(min_value=0.01, max_value=1000, allow_nan=False, allow_infinity=False),
    high=st.floats(min_value=0.01, max_value=1000, allow_nan=False, allow_infinity=False),
)
def test_limit_order_fill_conditions(limit: float, low: float, high: float) -> None:
    # Ensure low <= high and derive close in [low, high]
    lo, hi = (low, high) if low <= high else (high, low)
    close = (lo + hi) / 2.0

    sim = SimpleExecutionSimulator(slippage_bps=0)
    buy = Order(
        local_id="b", symbol="SPY", side="buy", type="limit", quantity=10, limit_price=limit
    )
    sell = Order(
        local_id="s", symbol="SPY", side="sell", type="limit", quantity=10, limit_price=limit
    )

    fb = sim.simulate_fill(order=buy, bar_close=close, bar_high=hi, bar_low=lo, bar_volume=1000)
    fs = sim.simulate_fill(order=sell, bar_close=close, bar_high=hi, bar_low=lo, bar_volume=1000)

    # Buy fills only if bar_low <= limit
    if lo <= limit:
        assert fb is not None
    else:
        assert fb is None

    # Sell fills only if bar_high >= limit
    if hi >= limit:
        assert fs is not None
    else:
        assert fs is None
