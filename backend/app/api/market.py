
import typing
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_market_provider
from app.schemas.market import Bar, QuoteSnapshot
from app.services.market.base import MarketProvider
from app.services.market.price_cache import price_cache

router = APIRouter()

@router.get("/api/market/quotes")
async def get_quotes(tickers: str | None = Query(None)) -> dict[str, QuoteSnapshot]:
    """Latest quotes snapshot."""
    all_quotes = price_cache.get_all()
    if tickers:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        return {t: all_quotes[t] for t in ticker_list if t in all_quotes}
    return all_quotes

@router.get("/api/market/bars/{ticker}", response_model=list[Bar])
async def get_bars(
    ticker: str,
    timeframe: str = "1D",
    limit: int = 100,
    provider: Annotated[MarketProvider, Depends(get_market_provider)] = None  # type: ignore
) -> list[Bar]:
    """OHLCV history."""
    # Normalize frontend timeframe names to internal format
    tf_map = {"1Min": "1m", "5Min": "5m", "1Hour": "1h", "1Day": "1D"}
    normalized_tf = tf_map.get(timeframe, timeframe)
    try:
        return await provider.get_bars(ticker=ticker.upper(), timeframe=normalized_tf, limit=limit)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))

from app.services.indicators import IndicatorService


@router.get("/api/market/indicators/{ticker}")
async def get_indicators(
    ticker: str,
    timeframe: str = "1D",
    provider: Annotated[MarketProvider, Depends(get_market_provider)] = None  # type: ignore
) -> dict[str, typing.Any]:
    """Latest indicator values + labels."""
    try:
        svc = IndicatorService(provider)
        return await svc.get_indicators(ticker=ticker.upper(), timeframe=timeframe)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))
