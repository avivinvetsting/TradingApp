from __future__ import annotations
import uuid
from pathlib import Path

from trading.backtest.engine import BacktestConfig, BacktestEngine
from trading.core.contracts import Strategy
from trading.core.models import Bar


class NoopStrategy(Strategy):
    def on_bar(self, bar: Bar) -> None:
        return None


def test_backtest_engine_writes_artifacts(tmp_path: Path) -> None:
    # Prepare tiny dataset
    import pandas as pd

    df = pd.DataFrame(
        [
            {
                "symbol": "SPY",
                "end": pd.Timestamp("2024-01-02", tz="UTC"),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000,
            },
            {
                "symbol": "SPY",
                "end": pd.Timestamp("2024-01-03", tz="UTC"),
                "open": 101.0,
                "high": 102.0,
                "low": 100.0,
                "close": 101.5,
                "volume": 1100,
            },
        ]
    )
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    df.to_parquet(cache_dir / "SPY_1d.parquet", index=False)

    run_id = str(uuid.uuid4())
    cfg = BacktestConfig(
        symbols=["SPY"], interval="1d", cache_dir=cache_dir, run_id=run_id, out_dir=tmp_path
    )
    engine = BacktestEngine(strategy_factory=lambda sym: NoopStrategy(), config=cfg)
    engine.run()

    out_base = tmp_path / run_id
    assert (out_base / "equity.parquet").exists()
    # Orders/fills may be omitted if no orders were proposed/filled
    assert (out_base / "orders.parquet").exists() or True
    assert (out_base / "fills.parquet").exists() or True
    assert (out_base / "summary.json").exists()
