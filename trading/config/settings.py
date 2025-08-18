from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional, Any

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml  # type: ignore[import-untyped]


class StrategyConfig(BaseModel):  # type: ignore[misc]
    name: str
    params: Dict[str, Any]


class DataConfig(BaseModel):  # type: ignore[misc]
    source: str
    cache_dir: Path
    ib_host: Optional[str] = None
    ib_port: Optional[int] = None
    ib_client_id: Optional[int] = None


class RiskConfig(BaseModel):  # type: ignore[misc]
    max_gross_exposure: float
    per_symbol_notional_cap: float
    market_calendar: str = "XNYS"
    daily_loss_cap: Optional[float] = None


class ExecutionConfig(BaseModel):  # type: ignore[misc]
    default_order_type: str = "limit"
    slippage_bps: int = 1
    commission_fixed: float = 1.0


class AppSettings(BaseSettings):  # type: ignore[misc]
    model_config = SettingsConfigDict(
        env_prefix="TRADE_", env_nested_delimiter="__", extra="ignore"
    )

    run_id: Optional[str] = None
    timeframe: str
    symbols: List[str]

    data: DataConfig
    risk: RiskConfig
    execution: ExecutionConfig
    strategy: StrategyConfig


def load_settings(path: str | Path) -> AppSettings:
    with open(path, "r", encoding="utf-8") as f:
        raw: Dict[str, Any] = yaml.safe_load(f)
    return AppSettings.model_validate(raw)  # type: ignore[no-any-return]
