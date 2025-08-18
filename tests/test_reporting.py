from __future__ import annotations
import json
from pathlib import Path

import pandas as pd

from trading.reporting.report import generate_html_report


def test_generate_html_report(tmp_path: Path) -> None:
    # Minimal run dir with equity.parquet and summary.json
    run = tmp_path / "r"
    (run / "reports").mkdir(parents=True, exist_ok=True)

    eq = pd.DataFrame(
        [
            {"ts": "2024-01-02T00:00:00+00:00", "equity": 100000.0},
            {"ts": "2024-01-03T00:00:00+00:00", "equity": 100100.0},
        ]
    )
    eq.to_parquet(run / "equity.parquet", index=False)
    (run / "summary.json").write_text(
        json.dumps({"run_id": "r", "symbols": ["SPY"], "interval": "1d", "metrics": {}}),
        encoding="utf-8",
    )

    out = generate_html_report(run)
    assert out.exists()
    assert out.name == "report.html"
