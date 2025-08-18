from __future__ import annotations
from pathlib import Path

from trading.config.settings import load_settings, AppSettings


def test_load_settings_example() -> None:
    cfg_path = Path("config.example.yaml")
    settings = load_settings(cfg_path)
    assert isinstance(settings, AppSettings)
    assert settings.timeframe in ("1D", "1d", "daily")
    assert len(settings.symbols) >= 1
    assert settings.data.cache_dir is not None
    assert settings.execution.slippage_bps >= 0
    assert settings.risk.per_symbol_notional_cap > 0
