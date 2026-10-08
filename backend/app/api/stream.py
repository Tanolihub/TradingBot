import asyncio
import json
import typing

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from app.core.db import AsyncSessionLocal
from app.services.market.hub import market_hub
from app.services.market.price_cache import price_cache
from app.services.portfolio import PortfolioService

router = APIRouter()

async def event_generator(request: Request) -> typing.AsyncGenerator[dict[str, str], None]:
    q = market_hub.subscribe()

    try:
        # 1. Send snapshot (includes quotes, status AND portfolio)
        portfolio_data = None
        try:
            async with AsyncSessionLocal() as session:
                svc = PortfolioService(session)
                snap = await svc.get_portfolio_snapshot()
                portfolio_data = json.loads(snap.model_dump_json())
        except Exception:  # noqa: BLE001
            pass

        snapshot = {
            "quotes": {k: v.model_dump(mode='json') for k, v in price_cache.get_all().items()},
            "status": market_hub.market_status.model_dump(),
            "portfolio": portfolio_data
        }
        yield {
            "event": "snapshot",
            "data": json.dumps(snapshot)
        }

        # 2. Listen for events
        while True:
            if await request.is_disconnected():
                break

            try:
                # Use asyncio.wait_for to occasionally yield a ping
                msg = await asyncio.wait_for(q.get(), timeout=15.0)
                # sse_starlette expects dicts, msg is formatted string
                # We can just yield the raw msg, but EventSourceResponse formats dicts.
                # msg format: "event: ...\ndata: ...\n\n" from hub.
                # Since EventSourceResponse takes a dict, we should have hub just put dicts.
                yield msg
            except TimeoutError:
                yield {
                    "event": "ping",
                    "data": ""
                }
    finally:
        market_hub.unsubscribe(q)

@router.get("/api/stream")
async def stream_market_data(request: Request) -> EventSourceResponse:
    return EventSourceResponse(event_generator(request))
