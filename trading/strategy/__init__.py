from .registry import register_strategy, get_strategy_names

# Import built-in example strategies so they register on import
from .examples import ma_crossover as _ma_crossover  # noqa: F401
from .examples import momentum as _momentum  # noqa: F401

__all__ = ["register_strategy", "get_strategy_names"]
