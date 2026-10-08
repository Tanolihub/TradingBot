
from app.services.market.base import MarketProvider

_market_provider: MarketProvider | None = None

def set_market_provider(provider: MarketProvider) -> None:
    global _market_provider
    _market_provider = provider

def get_market_provider() -> MarketProvider:
    if not _market_provider:
        raise RuntimeError("Market provider not initialized")
    return _market_provider
