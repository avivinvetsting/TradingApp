from __future__ import annotations
import json
import uuid
from pathlib import Path

import pandas as pd

from trading.backtest.engine import BacktestConfig, BacktestEngine
from trading.core.contracts import Strategy
from trading.core.models import Bar


class NoopStrategy(Strategy):
    def on_bar(self, bar: Bar) -> None:
        return None


def test_summary_snapshot_no_trades(tmp_path: Path) -> None:
    # Prepare a deterministic two-bar dataset (no trades -> flat equity)
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
        symbols=["SPY"],
        interval="1d",
        cache_dir=cache_dir,
        run_id=run_id,
        out_dir=tmp_path,
        config_hash="testhash000000000",
    )
    engine = BacktestEngine(strategy_factory=lambda sym: NoopStrategy(), config=cfg)
    engine.run()

    out_base = tmp_path / run_id
    # Ledgers present
    assert (out_base / "equity.parquet").exists()
    assert (out_base / "bars.parquet").exists()

    # Summary snapshot: keys and stable values for no-trade run
    j = json.loads((out_base / "summary.json").read_text("utf-8"))
    assert j["run_id"] == run_id
    assert j["symbols"] == ["SPY"]
    assert j["interval"] == "1d"
    assert j["config_hash"] == "testhash000000000"
    # git_sha may be None in CI/tmp; only assert presence
    assert "git_sha" in j
    # Metrics should exist and be zeros for flat equity
    m = j.get("metrics") or {}
    for key in [
        "cagr",
        "sharpe",
        "sortino",
        "max_drawdown",
        "calmar",
        "hit_rate",
    ]:
        assert key in m
        assert abs(float(m[key])) < 1e-12

    # Observability section should include counters and timer stats
    obs = j.get("observability") or {}
    assert "counters" in obs and "timers" in obs
    ctrs = obs["counters"]
    assert ctrs["bars"] >= 2
    assert ctrs["orders_proposed"] >= 0
    assert ctrs["orders_approved"] >= 0
    assert ctrs["fills"] >= 0
    timers = obs["timers"]["bar_loop_ms"]
    assert "count" in timers and "avg" in timers and "p50" in timers and "p95" in timers
