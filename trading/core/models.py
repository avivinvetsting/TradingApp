from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Instrument:
    symbol: str


@dataclass
class Bar:
    symbol: str
    end: datetime  # bar close (UTC)
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class Order:
    local_id: str
    symbol: str
    side: str  # "buy" | "sell"
    type: str  # "market" | "limit"
    quantity: int
    limit_price: Optional[float] = None
    tif: str = "DAY"
    broker_id: Optional[str] = None


@dataclass
class Fill:
    order_local_id: str
    ts: datetime
    qty: int
    price: float
    commission: float


@dataclass
class Position:
    symbol: str
    qty: int
    avg_price: float


@dataclass
class PortfolioSnapshot:
    ts: datetime
    cash: float
    equity: float
    unrealized_pnl: float
    realized_pnl: float
