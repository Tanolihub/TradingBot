from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.portfolio import Portfolio, WatchlistItem


async def seed_database(session: AsyncSession) -> None:
    # 1. Seed portfolio
    stmt = select(Portfolio).where(Portfolio.id == 1)
    result = await session.execute(stmt)
    portfolio = result.scalar_one_or_none()

    if not portfolio:
        portfolio = Portfolio(
            id=1,
            cash=settings.STARTING_CASH,
            starting_cash=settings.STARTING_CASH
        )
        session.add(portfolio)
        await session.commit()

    # 2. Seed watchlist
    default_tickers = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "AMD", "SPY", "QQQ"]
    for i, ticker in enumerate(default_tickers):
        stmt2 = select(WatchlistItem).where(
            WatchlistItem.portfolio_id == 1,
            WatchlistItem.ticker == ticker
        )
        result2 = await session.execute(stmt2)
        item2 = result2.scalar_one_or_none()

        if not item2:
            item_new = WatchlistItem(
                portfolio_id=1,
                ticker=ticker,
                sort_order=i
            )
            session.add(item_new)

    await session.commit()
