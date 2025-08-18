from typing import Optional
import uuid
from pathlib import Path
import hashlib
import typer

app = typer.Typer(help="Trading CLI")
fixtures_app = typer.Typer(help="Data fixtures utilities")
ops_app = typer.Typer(help="Ops utilities")


def plan() -> None:
    """Show high-level plan location."""
    typer.echo("See PROJECT_PLAN.md and DETAILED_PHASE_PLAN.md")


def backtest(
    config: str = typer.Option(..., "--config", help="Path to YAML config"),
    run_id: Optional[str] = typer.Option(None, "--run-id", help="Explicit run id; default uuid4"),
    json_logs: bool = typer.Option(False, "--json-logs", help="Emit JSON logs to stdout"),
    out_dir: Optional[str] = typer.Option(None, "--out-dir", help="Output base directory for run artifacts (default 'runs')"),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level: DEBUG, INFO, WARNING, ERROR"),
    no_autodownload: bool = typer.Option(False, "--no-autodownload", help="Disable auto-download of missing caches"),
    heartbeat_every: int = typer.Option(100, "--heartbeat-every", help="Emit heartbeat every N bars"),
) -> None:
    """Run a backtest using config (simple runner for Parquet cache)."""
    from trading.config import load_settings
    from trading.backtest.engine import BacktestConfig, BacktestEngine
    from trading.observability.logging import get_logger, configure_logging

    settings = load_settings(config)
    run = run_id or str(uuid.uuid4())
    interval = (
        "1d"
        if settings.timeframe.lower() in {"1d", "1day", "daily"}
        else settings.timeframe.lower()
    )
    cfg = BacktestConfig(
        symbols=settings.symbols,
        interval=interval,
        cache_dir=str(settings.data.cache_dir),
        run_id=run,
        out_dir=out_dir or "runs",
        config_hash=hashlib.sha256(Path(config).read_bytes()).hexdigest()[:16],
        slippage_bps=settings.execution.slippage_bps,
        commission_fixed=settings.execution.commission_fixed,
        per_symbol_notional_cap=settings.risk.per_symbol_notional_cap,
        heartbeat_every=heartbeat_every,
    )

    # Auto-download missing caches into the configured cache_dir
    if not no_autodownload:
        try:
            from pathlib import Path
            from trading.data.fixtures import download_yf_bars

            cache_dir = Path(cfg.cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)
            missing: list[str] = []
            for sym in cfg.symbols:
                if not (cache_dir / f"{sym}_{cfg.interval}.parquet").exists():
                    missing.append(sym)
            if missing:
                logger = get_logger("trading.backtest", json=json_logs)
                logger.warning(
                    "auto-downloading missing data",
                    extra={"symbols": missing, "cache_dir": str(cache_dir)},
                )
                download_yf_bars(
                    missing, interval=cfg.interval, start="2024-01-01", out_dir=str(cache_dir)
                )
        except Exception as exc:
            logger = get_logger("trading.backtest", json=json_logs)
            logger.warning("auto-download skipped", extra={"error": str(exc)})

    from trading.core.contracts import Strategy as StrategyABC

    def strategy_factory(symbol: str) -> StrategyABC:
        # Use a no-op strategy placeholder; users will plug in real ones later
        from trading.core.contracts import Strategy
        from trading.core.models import Bar

        class NoopStrategy(Strategy):
            def on_bar(self, bar: Bar):
                return None

        return NoopStrategy()

    # Logger
    import logging as _logging
    level = getattr(_logging, str(log_level).upper(), _logging.INFO)
    configure_logging(level=level, json=json_logs)
    logger = get_logger("trading.backtest").bind(run_id=run)
    logger.info("starting_backtest", symbols=cfg.symbols, interval=cfg.interval)

    engine = BacktestEngine(strategy_factory=strategy_factory, config=cfg, logger=logger)
    engine.run()
    logger.info("backtest_finished", out_dir=str(cfg.out_dir))
    # Generate HTML report
    try:
        from trading.reporting.report import generate_html_report

        out = generate_html_report(f"{cfg.out_dir}/{run}")
        logger.info("report_generated", path=str(out))
    except Exception as exc:
        logger.warning("report_generation_failed", error=str(exc))


def live(
    config: str = typer.Option(..., "--config", help="Path to YAML config"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Do not actually place orders"),
) -> None:
    """Run the live loop (MVP). In dry-run, only connectivity is checked."""
    from trading.config import load_settings

    settings = load_settings(config)
    if dry_run:
        try:
            from trading.live.connection import IBConnectionConfig, IBConnectionManager

            cfg = IBConnectionConfig(
                host=settings.data.ib_host or "127.0.0.1",
                port=settings.data.ib_port or 7497,
                client_id=settings.data.ib_client_id or 999,
            )

            import asyncio

            async def check() -> None:
                cm = IBConnectionManager(cfg)
                await cm.ensure_connected()
                print("IB: connected")
                await cm.disconnect()
                print("IB: disconnected")

            asyncio.run(check())
        except Exception as exc:
            print(f"Live dry-run failed: {exc}")
        return
    else:
        print("Live trading loop not implemented yet (Phase 3 WIP)")


def fixtures_download(
    symbols: list[str] = typer.Argument(..., help="Symbols to download, e.g., SPY QQQ"),
    interval: str = typer.Option("1d", "--interval", help="Interval: 1d, 1h, 1m (yf)"),
    start: str | None = typer.Option(None, "--start", help="Start date YYYY-MM-DD"),
    end: str | None = typer.Option(None, "--end", help="End date YYYY-MM-DD"),
    out_dir: str = typer.Option("data/cache/yf", "--out-dir", help="Output directory"),
) -> None:
    from trading.data.fixtures import download_yf_bars

    paths = download_yf_bars(symbols, interval=interval, start=start, end=end, out_dir=out_dir)
    if not paths:
        print("No data downloaded (check symbols/interval)")
    else:
        for p in paths:
            print(f"Saved {p}")


def prune(
    target: str = typer.Argument(..., help="'runs' or 'cache'"),
    keep_days: int = typer.Option(30, "--keep-days", help="Keep items newer than N days"),
    apply: bool = typer.Option(False, "--apply", help="Actually delete (default is dry-run)"),
) -> None:
    from trading.core.retention import prune_directories

    base = {
        "runs": "runs",
        "cache": "data/cache",
    }.get(target)
    if base is None:
        raise typer.BadParameter("target must be 'runs' or 'cache'")
    removed = prune_directories(base, keep_days=keep_days, apply=apply)
    action = "Removed" if apply else "Would remove"
    for path in removed:
        print(f"{action}: {path}")


app.add_typer(fixtures_app, name="fixtures")
app.add_typer(ops_app, name="ops")

# Register commands to satisfy mypy without decorator complaints
app.command()(plan)
app.command()(backtest)
app.command()(live)
fixtures_app.command("download")(fixtures_download)
ops_app.command("prune")(prune)
