import asyncio
import json

from app.schemas.market import MarketStatus, Tick


class MarketHub:
    def __init__(self) -> None:
        self.clients: set[asyncio.Queue[dict[str, str]]] = set()
        self.market_status = MarketStatus(market="closed", feed="down")

        # Buffer for coalescing ticks. Maps ticker -> Tick
        self._tick_buffer: dict[str, Tick] = {}
        self._flush_task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if not self._flush_task or self._flush_task.done():
            self._flush_task = asyncio.create_task(self._flush_loop())

    def stop(self) -> None:
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()

    async def _flush_loop(self) -> None:
        """Flush the coalesced ticks 4 times per second (250ms)."""
        while True:
            try:
                await asyncio.sleep(0.25)
                if self._tick_buffer:
                    ticks = list(self._tick_buffer.values())
                    self._tick_buffer.clear()

                    event_data = json.dumps([t.model_dump(mode='json') for t in ticks])
                    await self.broadcast("tick", event_data)
            except asyncio.CancelledError:
                break
            except Exception:  # noqa: BLE001, S110
                pass

    def subscribe(self) -> asyncio.Queue[dict[str, str]]:
        # Bounded queue to drop messages if client is slow
        q: asyncio.Queue[dict[str, str]] = asyncio.Queue(maxsize=100)
        self.clients.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[dict[str, str]]) -> None:
        if q in self.clients:
            self.clients.remove(q)

    async def broadcast(self, event: str, data: str) -> None:
        msg = {"event": event, "data": data}
        for q in list(self.clients):
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                # Slow client, drop the message
                pass

    async def on_tick(self, tick: Tick) -> None:
        """Coalesce tick updates instead of sending immediately."""
        self._tick_buffer[tick.ticker] = tick

    async def update_status(self, market: str | None = None, feed: str | None = None) -> None:
        changed = False
        if market and self.market_status.market != market:
            self.market_status.market = market # type: ignore
            changed = True
        if feed and self.market_status.feed != feed:
            self.market_status.feed = feed # type: ignore
            changed = True

        if changed:
            await self.broadcast("status", self.market_status.model_dump_json())

market_hub = MarketHub()
