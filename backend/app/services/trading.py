import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import (
    err_insufficient_funds,
    err_insufficient_shares,
    err_price_unavailable,
    err_unknown_ticker,
)
from app.models.portfolio import Portfolio, Position, Trade
from app.schemas.portfolio import TradeResult
from app.services.market.hub import market_hub
from app.services.market.price_cache import price_cache
from app.services.portfolio import PortfolioService

ALLOWED_TICKERS = {"AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "AMD", "SPY", "QQQ"}

class TradingEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.portfolio_service = PortfolioService(session)

    async def execute_market_order(
        self,
        portfolio_id: int,
        ticker: str,
        side: str,
        quantity: int,
        source: str,
        idempotency_key: str | None = None,
        chat_message_id: int | None = None
    ) -> TradeResult:
        if ticker not in ALLOWED_TICKERS:
            raise err_unknown_ticker(ticker)

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if idempotency_key:
            stmt = select(Trade).where(Trade.idempotency_key == idempotency_key)
            res = await self.session.execute(stmt)
            existing_trade = res.scalar_one_or_none()
            if existing_trade:
                return TradeResult(
                    id=existing_trade.id,
                    ticker=existing_trade.ticker,
                    side=existing_trade.side,
                    quantity=existing_trade.quantity,
                    price=existing_trade.price,
                    notional=existing_trade.notional,
                    realized_pnl=existing_trade.realized_pnl,
                    executed_at=existing_trade.executed_at,
                    source=existing_trade.source
                )

        quote = price_cache.get(ticker)
        if not quote:
            raise err_price_unavailable(ticker)

        # Check staleness
        now = datetime.now(UTC)
        age = (now - quote.ts).total_seconds()

        # If market is open and price is older than threshold, reject
        if market_hub.market_status.market == "open" and age > settings.STALE_PRICE_SECONDS:
            raise err_price_unavailable(ticker)

        current_price = Decimal(str(quote.price))
        notional = current_price * Decimal(quantity)

        # Start transaction with FOR UPDATE
        stmt_port = select(Portfolio).where(Portfolio.id == portfolio_id).with_for_update()
        res_port = await self.session.execute(stmt_port)
        portfolio = res_port.scalar_one_or_none()
        if not portfolio:
            raise ValueError("Portfolio not found")

        stmt_pos = select(Position).where(
            Position.portfolio_id == portfolio_id,
            Position.ticker == ticker
        ).with_for_update()
        res_pos = await self.session.execute(stmt_pos)
        position = res_pos.scalar_one_or_none()

        realized_pnl = None

        if side == "buy":
            if portfolio.cash < notional:
                raise err_insufficient_funds(float(portfolio.cash), float(notional))

            portfolio.cash -= notional

            if position:
                total_cost = (position.avg_cost * Decimal(position.quantity)) + notional
                new_qty = position.quantity + quantity
                position.avg_cost = total_cost / Decimal(new_qty)
                position.quantity = new_qty
            else:
                position = Position(
                    portfolio_id=portfolio_id,
                    ticker=ticker,
                    quantity=quantity,
                    avg_cost=current_price
                )
                self.session.add(position)

        elif side == "sell":
            if not position or position.quantity < quantity:
                have = position.quantity if position else 0
                raise err_insufficient_shares(ticker, have, quantity)

            portfolio.cash += notional
            realized_pnl = (current_price - position.avg_cost) * Decimal(quantity)

            position.quantity -= quantity
            if position.quantity == 0:
                await self.session.delete(position)
        else:
            raise ValueError(f"Invalid side: {side}")

        trade = Trade(
            id=uuid.uuid4(),
            portfolio_id=portfolio_id,
            ticker=ticker,
            side=side,
            quantity=quantity,
            price=current_price,
            notional=notional,
            realized_pnl=realized_pnl,
            source=source,
            chat_message_id=chat_message_id,
            idempotency_key=idempotency_key
        )
        self.session.add(trade)

        # Flush before commit to catch any integrity errors
        await self.session.flush()

        result = TradeResult(
            id=trade.id,
            ticker=trade.ticker,
            side=trade.side,
            quantity=trade.quantity,
            price=trade.price,
            notional=trade.notional,
            realized_pnl=trade.realized_pnl,
            executed_at=trade.executed_at,
            source=trade.source
        )

        await self.session.commit()

        # Broadcast portfolio update
        await self.portfolio_service.broadcast_portfolio(portfolio_id)

        return result
