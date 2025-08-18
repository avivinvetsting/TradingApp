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
