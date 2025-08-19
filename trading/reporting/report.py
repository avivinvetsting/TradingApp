from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import json
import pandas as pd
import plotly.graph_objs as go
from jinja2 import Environment, FileSystemLoader


@dataclass
class ReportInputs:
    run_dir: Path
    summary: Dict[str, Any]
    equity: pd.DataFrame


def _compute_drawdown(equity: pd.Series) -> pd.Series:
    roll_max = equity.cummax()
    dd = equity / roll_max - 1.0
    return dd


def load_report_inputs(run_dir: Path) -> ReportInputs:
    with open(run_dir / "summary.json", "r", encoding="utf-8") as f:
        summary = json.load(f)
    import pyarrow.parquet as pq  # lazy import

    equity = pq.read_table(run_dir / "equity.parquet").to_pandas()
    equity = equity.sort_values("ts").reset_index(drop=True)
    return ReportInputs(run_dir=run_dir, summary=summary, equity=equity)


def generate_html_report(run_dir: str | Path) -> Path:
    run_path = Path(run_dir)
    ri = load_report_inputs(run_path)

    # Figures
    equity_series = pd.Series(ri.equity["equity"].to_list(), index=pd.to_datetime(ri.equity["ts"]))
    dd_series = _compute_drawdown(equity_series)

    fig_equity = go.Figure()
    fig_equity.add_trace(
        go.Scatter(x=equity_series.index, y=equity_series.values, mode="lines", name="Equity")
    )
    fig_equity.update_layout(title="Equity Curve", xaxis_title="Time", yaxis_title="Equity")

    fig_dd = go.Figure()
    fig_dd.add_trace(
        go.Scatter(x=dd_series.index, y=dd_series.values, mode="lines", name="Drawdown")
    )
    fig_dd.update_layout(title="Drawdown", xaxis_title="Time", yaxis_title="Drawdown")

    equity_html = fig_equity.to_html(full_html=False, include_plotlyjs="cdn")
    dd_html = fig_dd.to_html(full_html=False, include_plotlyjs=False)

    # Template
    template_dir = Path(__file__).parent
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("report.html.j2")

    metrics = ri.summary.get("metrics", {}) or {}
    observability = ri.summary.get("observability", {}) or {}

    html = template.render(
        run_id=ri.summary.get("run_id"),
        symbols=", ".join(ri.summary.get("symbols", [])),
        interval=ri.summary.get("interval"),
        metrics=metrics,
        observability=observability,
        equity_plot=equity_html,
        drawdown_plot=dd_html,
    )

    out_dir = run_path / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "report.html"
    out_file.write_text(html, encoding="utf-8")
    return out_file
