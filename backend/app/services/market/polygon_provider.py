import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import httpx
import websockets
import websockets.client
from websockets.exceptions import ConnectionClosed

from app.core.config import settings
from app.schemas.market import Bar, QuoteSnapshot, Tick
from app.services.market.price_cache import price_cache

logger = logging.getLogger(__name__)

class PolygonProvider:
    def __init__(self) -> None:
        self.on_tick: Callable[[Tick], Awaitable[None]] | None = None
        self.tickers: set[str] = set()
        import typing
        self._ws: typing.Any = None
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._base_url = "https://api.polygon.io"
        self._ws_url = f"wss://{settings.POLYGON_WS_FEED}"
        self.api_key = settings.POLYGON_API_KEY

        # Keep track of connection status callbacks if needed, typically handled via market_hub
        # The hub will update its status. We can just log here or trigger a callback.
        self.on_status_change: Callable[[str, str], Awaitable[None]] | None = None

    async def _update_status(self, market: str, feed: str) -> None:
        if self.on_status_change:
            await self.on_status_change(market, feed)

    async def start(self, tickers: set[str]) -> None:
        self.tickers = tickers
        self._running = True

        # Load previous close for these tickers to calculate change
        await self._load_previous_closes(tickers)

        if not self._task or self._task.done():
            self._task = asyncio.create_task(self._ws_loop())

    async def stop(self) -> None:
        self._running = False
        if self._ws:
            await self._ws.close()
        if self._task and not self._task.done():
            self._task.cancel()

    async def _load_previous_closes(self, tickers: set[str]) -> None:
        if not self.api_key:
            return

        async with httpx.AsyncClient() as client:
            for ticker in tickers:
                try:
                    resp = await client.get(
                        f"{self._base_url}/v2/aggs/ticker/{ticker}/prev",
                        params={"adjusted": "true", "apiKey": self.api_key}
                    )
                    data = resp.json()
                    if data.get("results"):
                        prev_close = data["results"][0]["c"]
                        # We just store a mock quote with 0 change for now until first tick
                        price_cache.update(ticker, QuoteSnapshot(
                            price=prev_close,
                            change=0.0,
                            change_pct=0.0,
                            ts=datetime.now(UTC)
                        ))
                except Exception as e:  # noqa: BLE001
                    logger.error(f"Failed to fetch prev close for {ticker}: {e}")

    async def subscribe(self, tickers: set[str]) -> None:
        new_tickers = tickers - self.tickers
        if new_tickers:
            self.tickers.update(new_tickers)
            await self._load_previous_closes(new_tickers)
            if self._ws and self._ws.open:
                subs = ",".join(f"T.{t}" for t in new_tickers)
                await self._ws.send(json.dumps({"action": "subscribe", "params": subs}))

    async def unsubscribe(self, tickers: set[str]) -> None:
        removed = tickers.intersection(self.tickers)
        if removed:
            self.tickers -= removed
            if self._ws and self._ws.open:
                unsubs = ",".join(f"T.{t}" for t in removed)
                await self._ws.send(json.dumps({"action": "unsubscribe", "params": unsubs}))

    async def get_bars(self, ticker: str, timeframe: str, limit: int) -> list[Bar]:
        if not self.api_key:
            return []

        multiplier = 1
        timespan = "day"
        if timeframe == "1m":
            multiplier = 1
            timespan = "minute"
        elif timeframe == "5m":
            multiplier = 5
            timespan = "minute"
        elif timeframe == "1h":
            multiplier = 1
            timespan = "hour"

        # Basic date range
        end = datetime.now(UTC)
        start = end - timedelta(days=limit if timespan == "day" else limit / 24)

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._base_url}/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{start.strftime('%Y-%m-%d')}/{end.strftime('%Y-%m-%d')}",
                params={"adjusted": "true", "sort": "asc", "limit": limit, "apiKey": self.api_key}
            )
            data = resp.json()
            bars = []
            for res in data.get("results", []):
                bars.append(Bar(
                    timestamp=datetime.fromtimestamp(res["t"]/1000, tz=UTC),
                    open=res["o"],
                    high=res["h"],
                    low=res["l"],
                    close=res["c"],
                    volume=res["v"]
                ))
            return bars

    async def _ws_loop(self) -> None:
        retry_delay = 1.0
        while self._running:
            try:
                await self._update_status("open", "reconnecting")
                async with websockets.connect(self._ws_url) as ws:
                    self._ws = ws

                    # Polygon sends an initial "connected" message upon successful TCP connect
                    _ = json.loads(await ws.recv())

                    # Auth
                    await ws.send(json.dumps({"action": "auth", "params": self.api_key}))
                    auth_resp = json.loads(await ws.recv())
                    if auth_resp[0].get("status") == "auth_success":
                        await self._update_status("open", "connected")
                        retry_delay = 1.0

                        # Subscribe
                        if self.tickers:
                            subs = ",".join(f"T.{t}" for t in self.tickers)
                            await ws.send(json.dumps({"action": "subscribe", "params": subs}))

                        # Listen
                        while self._running:
                            msg = await ws.recv()
                            data = json.loads(msg)
                            for event in data:
                                if event.get("ev") == "T":
                                    ticker = event["sym"]
                                    price = event["p"]

                                    # Calculate change
                                    cached = price_cache.get(ticker)
                                    prev_close = cached.price - cached.change if cached else price

                                    change = price - prev_close
                                    change_pct = (change / prev_close * 100) if prev_close > 0 else 0.0

                                    now = datetime.fromtimestamp(event["t"]/1000, tz=UTC)

                                    tick = Tick(
                                        ticker=ticker,
                                        price=price,
                                        change=round(change, 2),
                                        change_pct=round(change_pct, 2),
                                        ts=now
                                    )

                                    price_cache.update(ticker, QuoteSnapshot(
                                        price=price,
                                        change=round(change, 2),
                                        change_pct=round(change_pct, 2),
                                        ts=now
                                    ))

                                    if self.on_tick:
                                        await self.on_tick(tick)
                    else:
                        logger.error(f"Polygon auth failed: {auth_resp}")
                        await asyncio.sleep(5)

            except (ConnectionClosed, Exception) as e:  # noqa: BLE001
                logger.error(f"Polygon WS error: {e}")
                self._ws = None
                await self._update_status("open", "down")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60.0)
