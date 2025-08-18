import importlib


def test_cli_imports() -> None:
    # Ensure CLI module imports without side effects errors
    importlib.import_module("trading.__main__")


def test_strategy_registry_populated_on_import() -> None:
    names = importlib.import_module("trading.strategy").get_strategy_names()
    assert set(["ma_crossover", "momentum"]) <= set(names)
