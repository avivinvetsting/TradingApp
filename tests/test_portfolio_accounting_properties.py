from __future__ import annotations

from datetime import datetime, timezone

from hypothesis import given, strategies as st

from trading.core.models import Fill
from trading.portfolio.accounting import PortfolioState


@given(
    buys=st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=20),
    buy_prices=st.lists(
        st.floats(min_value=0.01, max_value=10000, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=20,
    ),
    sell_qty=st.integers(min_value=0, max_value=1000),
    sell_price=st.floats(min_value=0.01, max_value=10000, allow_nan=False, allow_infinity=False),
    commission=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
)
def test_cash_equity_and_positions_invariants(
    buys: list[int],
    buy_prices: list[float],
    sell_qty: int,
    sell_price: float,
    commission: float,
) -> None:
    n = min(len(buys), len(buy_prices))
    buys = buys[:n]
    buy_prices = buy_prices[:n]

    pf = PortfolioState(cash=1_000_000.0)
    symbol = "SPY"

    total_bought = 0
    now = datetime.now(timezone.utc)

    for i, (qty, price) in enumerate(zip(buys, buy_prices)):
        fill = Fill(order_local_id=f"b{i}", ts=now, qty=qty, price=price, commission=commission)
        pf.apply_fill(fill=fill, price=price, symbol=symbol, commission=commission)
        total_bought += qty

    sell_qty = min(sell_qty, total_bought)
    if sell_qty > 0:
        sfill = Fill(
            order_local_id="s", ts=now, qty=-sell_qty, price=sell_price, commission=commission
        )
        pf.apply_fill(fill=sfill, price=sell_price, symbol=symbol, commission=commission)

    # Quantity never negative
    assert pf.positions[symbol].qty >= 0

    # Equity equals cash + position market value at mark
    snap = pf.snapshot(marks={symbol: sell_price})
    expected_equity = snap.cash + pf.positions[symbol].qty * sell_price
    assert abs(snap.equity - expected_equity) < 1e-6


@given(
    qty=st.integers(min_value=1, max_value=10_000),
    buy_price=st.floats(min_value=0.01, max_value=10_000, allow_nan=False, allow_infinity=False),
    sell_price=st.floats(min_value=0.01, max_value=10_000, allow_nan=False, allow_infinity=False),
    commission=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
)
def test_round_trip_realized_pnl_definition(
    qty: int, buy_price: float, sell_price: float, commission: float
) -> None:
    pf = PortfolioState(cash=1_000_000.0)
    symbol = "QQQ"
    now = datetime.now(timezone.utc)

    b = Fill(order_local_id="b", ts=now, qty=qty, price=buy_price, commission=commission)
    pf.apply_fill(fill=b, price=buy_price, symbol=symbol, commission=commission)

    s = Fill(order_local_id="s", ts=now, qty=-qty, price=sell_price, commission=commission)
    pf.apply_fill(fill=s, price=sell_price, symbol=symbol, commission=commission)

    expected_realized = (sell_price - buy_price) * qty - commission
    assert abs(pf.realized_pnl - expected_realized) < 1e-6
