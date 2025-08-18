from __future__ import annotations
from typing import Callable, Dict, Type

from trading.core.contracts import Strategy


_STRATEGY_REGISTRY: Dict[str, Type[Strategy]] = {}


def register_strategy(name: str) -> Callable[[Type[Strategy]], Type[Strategy]]:
    def decorator(cls: Type[Strategy]) -> Type[Strategy]:
        key = name.lower()
        if key in _STRATEGY_REGISTRY:
            raise ValueError(f"Strategy '{name}' already registered")
        _STRATEGY_REGISTRY[key] = cls
        return cls

    return decorator


def get_strategy_names() -> list[str]:
    return sorted(_STRATEGY_REGISTRY.keys())
