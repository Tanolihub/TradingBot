import typing
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, market, portfolio, stream, trades
from app.api.deps import set_market_provider
from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.core.seed import seed_database
from app.services.market.alpaca_provider import AlpacaProvider
from app.services.market.base import MarketProvider
from app.services.market.hub import market_hub
from app.services.market.mock_provider import MockProvider


@asynccontextmanager
async def lifespan(app: FastAPI) -> typing.AsyncGenerator[None, None]:
    # Seed DB
    async with AsyncSessionLocal() as session:
        await seed_database(session)

    # Start Hub
    market_hub.start()

    # Start Provider
    provider: MarketProvider
    if settings.MARKET_DATA_PROVIDER == "alpaca":
        provider = AlpacaProvider()
    else:
        provider = MockProvider()

    provider.on_tick = market_hub.on_tick
    # Pass hub's update status down to market provider if applicable
    if hasattr(provider, 'on_status_change'):
        provider.on_status_change = market_hub.update_status

    set_market_provider(provider)

    # Subscribe to default watchlist tickers
    default_tickers = {"AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "AMD", "SPY", "QQQ"}
    await provider.start(default_tickers)

    yield

    await provider.stop()
    market_hub.stop()

app = FastAPI(title="NeonPulse AI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream.router)
app.include_router(market.router)
app.include_router(portfolio.router)
app.include_router(trades.router)
app.include_router(chat.router)

@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "feed": market_hub.market_status.feed}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
