import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import httpx
import websockets
from websockets.exceptions import ConnectionClosed

from app.core.config import settings
from app.schemas.market import Bar, QuoteSnapshot, Tick
from app.services.market.price_cache import price_cache

logger = logging.getLogger(__name__)

class AlpacaProvider:
    def __init__(self) -> None:
        self.on_tick: Callable[[Tick], Awaitable[None]] | None = None
        self.tickers: set[str] = set()

        import typing
        self._ws: typing.Any = None
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._base_url = "https://data.alpaca.markets"
        self._ws_url = "wss://stream.data.alpaca.markets/v2/iex"
        self.api_key = settings.ALPACA_API_KEY
        self.api_secret = getattr(settings, "ALPACA_API_SECRET", "")

        self.on_status_change: Callable[[str, str], Awaitable[None]] | None = None

    async def _update_status(self, market: str, feed: str) -> None:
        if self.on_status_change:
            await self.on_status_change(market, feed)

    async def start(self, tickers: set[str]) -> None:
        self.tickers = tickers
        self._running = True

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

        headers = {"APCA-API-KEY-ID": self.api_key, "APCA-API-SECRET-KEY": self.api_secret}
        async with httpx.AsyncClient(timeout=10.0) as client:
            for ticker in tickers:
                try:
                    # Use the bars endpoint with 1Day timeframe to get latest close
                    end = datetime.now(UTC)
                    start = end - timedelta(days=5)
                    resp = await client.get(
                        f"{self._base_url}/v2/stocks/{ticker}/bars",
                        params={
                            "timeframe": "1Day",
                            "start": start.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            "end": end.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            "limit": 1,
                            "sort": "desc",
                            "feed": "iex"
                        },
                        headers=headers
                    )
                    if resp.status_code != 200:
                        logger.error(f"Alpaca prev close HTTP {resp.status_code} for {ticker}: {resp.text[:200]}")
                        continue
                    data = resp.json()
                    bars_list = data.get("bars", [])
                    if bars_list:
                        prev_close = bars_list[0]["c"]
                        price_cache.update(ticker, QuoteSnapshot(
                            price=prev_close,
                            change=0.0,
                            change_pct=0.0,
                            ts=datetime.now(UTC)
                        ))
                except Exception as e:
                    logger.error(f"Failed to fetch prev close for {ticker}: {e}")

    async def subscribe(self, tickers: set[str]) -> None:
        new_tickers = tickers - self.tickers
        if new_tickers:
            self.tickers.update(new_tickers)
            await self._load_previous_closes(new_tickers)
            if self._ws and self._ws.open:
                await self._ws.send(json.dumps({"action": "subscribe", "trades": list(new_tickers)}))

    async def unsubscribe(self, tickers: set[str]) -> None:
        removed = tickers.intersection(self.tickers)
        if removed:
            self.tickers -= removed
            if self._ws and self._ws.open:
                await self._ws.send(json.dumps({"action": "unsubscribe", "trades": list(removed)}))

    async def get_bars(self, ticker: str, timeframe: str, limit: int) -> list[Bar]:
        if not self.api_key:
            return []

        # Alpaca uses 1Min, 5Min, 1Hour, 1Day
        timeframe_map = {"1m": "1Min", "5m": "5Min", "1h": "1Hour", "1D": "1Day"}
        alpaca_tf = timeframe_map.get(timeframe, "1Day")

        end = datetime.now(UTC)
        if alpaca_tf in ("1Min", "5Min"):
            start = end - timedelta(hours=max(limit / 6, 24))
        elif alpaca_tf == "1Hour":
            start = end - timedelta(days=max(limit / 24, 7))
        else:
            start = end - timedelta(days=limit + 5)

        headers = {"APCA-API-KEY-ID": self.api_key, "APCA-API-SECRET-KEY": self.api_secret}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self._base_url}/v2/stocks/{ticker}/bars",
                params={
                    "timeframe": alpaca_tf,
                    "start": start.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "end": end.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "limit": limit,
                    "sort": "asc",
                    "feed": "iex"
                },
                headers=headers
            )
            if resp.status_code != 200:
                logger.error(f"Alpaca bars HTTP {resp.status_code} for {ticker}: {resp.text[:200]}")
                return []
            data = resp.json()
            bars = []
            for res in data.get("bars", []):
                # Alpaca timestamps can be ISO with timezone e.g. 2026-10-06T09:30:00Z
                ts_str = res["t"]
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    ts = datetime.now(UTC)
                bars.append(Bar(
                    timestamp=ts,
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

                    # Read the initial welcome message from Alpaca [{"T":"success","msg":"connected"}]
                    _ = json.loads(await ws.recv())

                    # Auth
                    await ws.send(json.dumps({
                        "action": "auth",
                        "key": self.api_key,
                        "secret": self.api_secret
                    }))

                    auth_resp = json.loads(await ws.recv())
                    if isinstance(auth_resp, list) and len(auth_resp) > 0 and auth_resp[0].get("T") == "success" and auth_resp[0].get("msg") == "authenticated":
                        await self._update_status("open", "connected")
                        retry_delay = 1.0

                        # Subscribe
                        if self.tickers:
                            await ws.send(json.dumps({"action": "subscribe", "trades": list(self.tickers)}))

                        # Listen
                        while self._running:
                            msg = await ws.recv()
                            data = json.loads(msg)
                            for event in data:
                                if event.get("T") == "t": # trade
                                    ticker = event["S"]
                                    price = event["p"]

                                    # Calculate change
                                    cached = price_cache.get(ticker)
                                    prev_close = cached.price - cached.change if cached else price

                                    change = price - prev_close
                                    change_pct = (change / prev_close * 100) if prev_close > 0 else 0.0

                                    now = datetime.now(UTC)
                                    try:
                                        ts_val = event.get("t", "")
                                        if isinstance(ts_val, str):
                                            now = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                                    except (ValueError, AttributeError):
                                        pass

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
                        logger.warning(f"Alpaca WS auth failed: {auth_resp}. Falling back to REST polling.")
                        await self._update_status("open", "connected")
                        # Fall back to REST-based polling
                        await self._rest_polling_loop()
                        return

            except (ConnectionClosed, Exception) as e:
                logger.error(f"Alpaca WS error: {e}")
                self._ws = None
                await self._update_status("open", "down")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60.0)

    async def _rest_polling_loop(self) -> None:
        """Fallback: poll Alpaca REST API for latest trades when WS is unavailable."""
        headers = {"APCA-API-KEY-ID": self.api_key, "APCA-API-SECRET-KEY": self.api_secret}
        while self._running:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    for ticker in list(self.tickers):
                        try:
                            resp = await client.get(
                                f"{self._base_url}/v2/stocks/{ticker}/trades/latest",
                                params={"feed": "iex"},
                                headers=headers
                            )
                            if resp.status_code != 200:
                                continue
                            data = resp.json()
                            trade_data = data.get("trade", {})
                            if not trade_data:
                                continue
                            price = trade_data["p"]

                            cached = price_cache.get(ticker)
                            prev_close = cached.price - cached.change if cached else price
                            change = price - prev_close
                            change_pct = (change / prev_close * 100) if prev_close > 0 else 0.0

                            now = datetime.now(UTC)
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
                        except Exception:  # noqa: BLE001
                            pass
            except Exception:  # noqa: BLE001
                pass
            await asyncio.sleep(5)  # Poll every 5 seconds
