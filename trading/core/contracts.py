from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

from .models import Bar, Order


class DataAdapter(ABC):
    @abstractmethod
    def latest_completed_bar(self, symbol: str, timeframe: str) -> Optional[Bar]:
        raise NotImplementedError


class BrokerAdapter(ABC):
    @abstractmethod
    def submit_order(self, order: Order) -> None:
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, local_id: str) -> None:
        raise NotImplementedError


class Strategy(ABC):
    @abstractmethod
    def on_bar(self, bar: Bar) -> Optional[Order]:
        raise NotImplementedError


class RiskManager(ABC):
    @abstractmethod
    def validate(self, proposed_order: Order) -> Optional[Order]:
        raise NotImplementedError


class ExecutionEngine(ABC):
    @abstractmethod
    def submit(self, order: Order) -> None:
        raise NotImplementedError


class Portfolio(ABC):
    @abstractmethod
    def snapshot(self) -> None:
        raise NotImplementedError
