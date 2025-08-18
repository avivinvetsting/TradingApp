from trading.strategy.registry import get_strategy_names


def test_registry_has_examples() -> None:
    names = get_strategy_names()
    assert "ma_crossover" in names
    assert "momentum" in names
