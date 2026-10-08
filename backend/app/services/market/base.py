from collections.abc import Awaitable, Callable
from typing import Protocol

from app.schemas.market import Bar, Tick


class MarketProvider(Protocol):
    on_tick: Callable[[Tick], Awaitable[None]] | None

    async def start(self, tickers: set[str]) -> None:
        """Start the provider and subscribe to initial tickers."""
        ...

    async def stop(self) -> None:
        """Stop the provider connection."""
        ...

    async def subscribe(self, tickers: set[str]) -> None:
        """Subscribe to additional tickers."""
        ...

    async def unsubscribe(self, tickers: set[str]) -> None:
        """Unsubscribe from tickers."""
        ...

    async def get_bars(self, ticker: str, timeframe: str, limit: int) -> list[Bar]:
        """Fetch historical bars."""
        ...
