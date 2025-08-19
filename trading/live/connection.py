from __future__ import annotations
from dataclasses import dataclass
from typing import Any, cast
import asyncio
import logging as _logging

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

try:  # lazy import; only used in live mode
    import ib_insync as ib
except Exception:  # pragma: no cover
    ib = None


@dataclass
class IBConnectionConfig:
    host: str
    port: int
    client_id: int


class IBConnectionManager:
    def __init__(self, config: IBConnectionConfig) -> None:
        if ib is None:
            raise RuntimeError(
                "ib_insync not available; install dependencies or run in backtest mode"
            )
        self.cfg = config
        self.ib: Any = (cast(Any, ib)).IB()
        # Prefer structlog if available, fall back to stdlib logging
        try:
            self._logger: Any = __import__("structlog").get_logger("trading.live.connection")
        except Exception:
            self._logger = _logging.getLogger("trading.live.connection")

    # Exponential backoff with jitter and cap to avoid thundering herd
    @retry(wait=wait_random_exponential(multiplier=1, max=30), stop=stop_after_attempt(5))  # type: ignore[misc]
    async def connect_with_backoff(self) -> None:
        timeout_seconds = 10.0
        try:
            # Log attempt (works for both structlog and stdlib)
            try:
                self._logger.info(
                    "connect_attempt",
                    host=self.cfg.host,
                    port=self.cfg.port,
                    client_id=self.cfg.client_id,
                    timeout_seconds=timeout_seconds,
                )
            except TypeError:
                self._logger.info(
                    "connect_attempt",
                    extra={
                        "host": self.cfg.host,
                        "port": self.cfg.port,
                        "client_id": self.cfg.client_id,
                        "timeout_seconds": timeout_seconds,
                    },
                )

            await asyncio.wait_for(
                self.ib.connectAsync(self.cfg.host, self.cfg.port, clientId=self.cfg.client_id),
                timeout=timeout_seconds,
            )
        except Exception as exc:
            # Log failure; exception will trigger retry by decorator
            try:
                self._logger.warning(
                    "connect_failed",
                    host=self.cfg.host,
                    port=self.cfg.port,
                    client_id=self.cfg.client_id,
                    error=str(exc),
                )
            except TypeError:
                self._logger.warning(
                    "connect_failed",
                    extra={
                        "host": self.cfg.host,
                        "port": self.cfg.port,
                        "client_id": self.cfg.client_id,
                        "error": str(exc),
                    },
                )
            raise
        else:
            try:
                self._logger.info(
                    "connect_success",
                    host=self.cfg.host,
                    port=self.cfg.port,
                    client_id=self.cfg.client_id,
                )
            except TypeError:
                self._logger.info(
                    "connect_success",
                    extra={
                        "host": self.cfg.host,
                        "port": self.cfg.port,
                        "client_id": self.cfg.client_id,
                    },
                )

    async def ensure_connected(self) -> None:
        if not self.ib.isConnected():
            await self.connect_with_backoff()

    async def disconnect(self) -> None:
        if self.ib.isConnected():
            self.ib.disconnect()

    def is_connected(self) -> bool:
        return bool(self.ib.isConnected())
