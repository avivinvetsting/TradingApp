from __future__ import annotations
from trading.core.models import Order
from trading.risk.manager import BasicRiskManager, RiskParams


def test_per_symbol_notional_cap_rejects_large_limit() -> None:
    rm = BasicRiskManager(
        RiskParams(max_gross_exposure=100000, per_symbol_notional_cap=1000.0),
        enable_session_gate=False,
    )
    order = Order(
        local_id="o1", symbol="SPY", side="buy", type="limit", quantity=100, limit_price=20.0
    )
    # Notional = 2000, cap = 1000 => reject
    assert rm.validate(order) is None


def test_accepts_small_limit() -> None:
    rm = BasicRiskManager(
        RiskParams(max_gross_exposure=100000, per_symbol_notional_cap=10000.0),
        enable_session_gate=False,
    )
    order = Order(
        local_id="o2", symbol="SPY", side="buy", type="limit", quantity=100, limit_price=20.0
    )
    assert rm.validate(order) is not None


def test_gross_exposure_cap_blocks_additional_notional() -> None:
    # Simulate existing gross exposure via callback
    current_gross = 900.0
    rm = BasicRiskManager(
        RiskParams(max_gross_exposure=1000.0, per_symbol_notional_cap=5000.0),
        get_gross_exposure=lambda: current_gross,
        enable_session_gate=False,
    )
    # New order notional 200 would exceed 1000 cap -> reject
    order = Order(
        local_id="o3", symbol="SPY", side="buy", type="limit", quantity=2, limit_price=100.0
    )
    assert rm.validate(order) is None


def test_daily_loss_cap_blocks_trading_when_breached() -> None:
    rm = BasicRiskManager(
        RiskParams(max_gross_exposure=1e9, per_symbol_notional_cap=1e9, daily_loss_cap=100.0),
        get_daily_realized_pnl=lambda: -150.0,
        enable_session_gate=False,
    )
    order = Order(
        local_id="o4", symbol="SPY", side="buy", type="limit", quantity=1, limit_price=10.0
    )
    assert rm.validate(order) is None
