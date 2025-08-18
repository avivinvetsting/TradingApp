from __future__ import annotations
from datetime import datetime, timezone

from trading.core.models import Fill
from trading.portfolio.accounting import PortfolioState


def test_buy_and_sell_updates_positions_and_pnl() -> None:
    pf = PortfolioState(cash=10000.0)

    # Buy 10 @ $100, $1 commission
    fill_buy = Fill(
        order_local_id="o1", ts=datetime.now(timezone.utc), qty=10, price=100.0, commission=1.0
    )
    pf.apply_fill(fill=fill_buy, price=100.0, symbol="SPY", commission=1.0)

    snap = pf.snapshot(marks={"SPY": 100.0})
    assert pf.positions["SPY"].qty == 10
    assert abs(pf.positions["SPY"].avg_price - 100.0) < 1e-9
    assert abs(snap.cash - (10000.0 - 100.0 * 10 - 1.0)) < 1e-9

    # Sell 4 @ $105, $1 commission
    fill_sell = Fill(
        order_local_id="o2", ts=datetime.now(timezone.utc), qty=-4, price=105.0, commission=1.0
    )
    pf.apply_fill(fill=fill_sell, price=105.0, symbol="SPY", commission=1.0)

    # Realized PnL = (105 - 100) * 4 - 1 = 19
    assert abs(pf.realized_pnl - 19.0) < 1e-9
    assert pf.positions["SPY"].qty == 6

    snap2 = pf.snapshot(marks={"SPY": 105.0})
    # Unrealized PnL = (105 - 100) * 6 = 30
    assert abs(snap2.unrealized_pnl - 30.0) < 1e-9
    # Cash = previous cash + proceeds - commission =  (10000 - 1000 - 1) + 105*4 - 1
    expected_cash = (10000.0 - 1000.0 - 1.0) + 420.0 - 1.0
    assert abs(pf.cash - expected_cash) < 1e-9
