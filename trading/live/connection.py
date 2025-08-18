from __future__ import annotations
from dataclasses import dataclass

from tenacity import retry, stop_after_attempt, wait_exponential

try:  # lazy import; only used in live mode
    from ib_insync import IB
except Exception:  # pragma: no cover
    IB = None


@dataclass
class IBConnectionConfig:
    host: str
    port: int
    client_id: int


class IBConnectionManager:
    def __init__(self, config: IBConnectionConfig) -> None:
        if IB is None:
            raise RuntimeError(
                "ib_insync not available; install dependencies or run in backtest mode"
            )
        self.cfg = config
        self.ib = IB()

    @retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(5))  # type: ignore[misc]
    async def connect_with_backoff(self) -> None:
        await self.ib.connectAsync(self.cfg.host, self.cfg.port, clientId=self.cfg.client_id)

    async def ensure_connected(self) -> None:
        if not self.ib.isConnected():
            await self.connect_with_backoff()

    async def disconnect(self) -> None:
        if self.ib.isConnected():
            self.ib.disconnect()

    def is_connected(self) -> bool:
        return bool(self.ib.isConnected())
