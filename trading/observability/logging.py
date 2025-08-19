from __future__ import annotations
import logging
from typing import Any


def configure_logging(level: int = logging.INFO, json: bool = False) -> None:
    if not json:
        root = logging.getLogger()
        if root.handlers:
            return
        root.setLevel(level)
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%SZ",
            )
        )
        root.addHandler(handler)
        root.propagate = False
        return

    try:
        import structlog

        processors: list[Any] = [
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
        structlog.configure(
            processors=processors,
            wrapper_class=structlog.make_filtering_bound_logger(level),
            cache_logger_on_first_use=True,
        )
        # Also attach a handler for stdlib loggers to avoid duplicate or missing handlers
        # when libraries use logging.getLogger(...).
        root = logging.getLogger()
        if not root.handlers:
            root.setLevel(level)
            root.addHandler(logging.StreamHandler())
    except Exception:
        # Fallback to stdlib text logging if structlog unavailable
        configure_logging(level=level, json=False)


def get_logger(name: str) -> Any:
    try:
        import structlog

        return structlog.get_logger(name)
    except Exception:
        return logging.getLogger(name)
