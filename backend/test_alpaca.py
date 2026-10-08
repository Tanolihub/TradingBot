import asyncio
from app.services.market.alpaca_provider import AlpacaProvider
from app.core.config import settings
from app.services.market.hub import market_hub

async def main():
    provider = AlpacaProvider()
    provider.api_key = settings.ALPACA_API_KEY
    provider.api_secret = settings.ALPACA_API_SECRET
    
    async def on_tick(tick):
        print(f"TICK: {tick}")
    
    provider.on_tick = on_tick
    print("Starting provider...")
    asyncio.create_task(provider.start({"AAPL", "TSLA"}))
    await asyncio.sleep(10)
    await provider.stop()

if __name__ == "__main__":
    asyncio.run(main())
