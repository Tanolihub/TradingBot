import asyncio
import random
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from app.schemas.market import Bar, QuoteSnapshot, Tick
from app.services.market.price_cache import price_cache


class MockProvider:
    def __init__(self) -> None:
        self.on_tick: Callable[[Tick], Awaitable[None]] | None = None
        self.on_status_change: Callable[[str, str], Awaitable[None]] | None = None
        self.tickers: set[str] = set()
        self._task: asyncio.Task[None] | None = None
        self._running = False

    async def start(self, tickers: set[str]) -> None:
        self.tickers = tickers
        self._running = True

        # Initialize price cache for new tickers
        for ticker in tickers:
            if not price_cache.get(ticker):
                base_price = 150.0 + random.random() * 50
                price_cache.update(ticker, QuoteSnapshot(
                    price=base_price,
                    change=0.0,
                    change_pct=0.0,
                    ts=datetime.now(UTC)
                ))

        if self.on_status_change:
            # We don't want to block startup, so run it in a task or just await if we were async
            # start is async so we can await it
            await self.on_status_change("open", "connected")

        if not self._task or self._task.done():
            self._task = asyncio.create_task(self._simulation_loop())

    async def stop(self) -> None:
        self._running = False
        if self.on_status_change:
            await self.on_status_change("closed", "disconnected")
        if self._task and not self._task.done():
            self._task.cancel()

    async def subscribe(self, tickers: set[str]) -> None:
        for ticker in tickers:
            if ticker not in self.tickers:
                self.tickers.add(ticker)
                if not price_cache.get(ticker):
                    base_price = 150.0 + random.random() * 50
                    price_cache.update(ticker, QuoteSnapshot(
                        price=base_price,
                        change=0.0,
                        change_pct=0.0,
                        ts=datetime.now(UTC)
                    ))

    async def unsubscribe(self, tickers: set[str]) -> None:
        self.tickers -= tickers

    async def get_bars(self, ticker: str, timeframe: str, limit: int) -> list[Bar]:
        bars = []
        now = datetime.now(UTC)
        current_price = 150.0

        cached = price_cache.get(ticker)
        if cached:
            current_price = cached.price

        for i in range(limit):
            bars.append(Bar(
                timestamp=now - timedelta(minutes=(limit - i)),
                open=current_price,
                high=current_price * 1.001,
                low=current_price * 0.999,
                close=current_price,
                volume=1000 + random.random() * 5000
            ))
        return bars

    async def _simulation_loop(self) -> None:
        while self._running:
            await asyncio.sleep(0.1) # Simulate high frequency

            if not self.tickers:
                continue

            # Pick a random ticker to update
            ticker = random.choice(list(self.tickers))
            cached = price_cache.get(ticker)
            if cached:
                # Random walk
                change_amt = cached.price * random.uniform(-0.001, 0.001)
                new_price = round(cached.price + change_amt, 2)

                # Keep within bounds just in case
                if new_price < 1:
                    new_price = 1.0

                new_change = round(cached.change + change_amt, 2)
                base_price = cached.price - cached.change if cached.change != 0 else cached.price
                new_change_pct = round((new_change / base_price) * 100, 2) if base_price > 0 else 0.0

                now = datetime.now(UTC)
                tick = Tick(
                    ticker=ticker,
                    price=new_price,
                    change=new_change,
                    change_pct=new_change_pct,
                    ts=now
                )

                price_cache.update(ticker, QuoteSnapshot(
                    price=new_price,
                    change=new_change,
                    change_pct=new_change_pct,
                    ts=now
                ))

                if self.on_tick:
                    await self.on_tick(tick)
