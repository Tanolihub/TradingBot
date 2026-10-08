
from app.schemas.market import QuoteSnapshot


class PriceCache:
    def __init__(self) -> None:
        self._cache: dict[str, QuoteSnapshot] = {}

    def update(self, ticker: str, quote: QuoteSnapshot) -> None:
        self._cache[ticker] = quote

    def get(self, ticker: str) -> QuoteSnapshot | None:
        return self._cache.get(ticker)

    def get_all(self) -> dict[str, QuoteSnapshot]:
        return self._cache.copy()

price_cache = PriceCache()
