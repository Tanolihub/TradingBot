from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import ChatMessage, Portfolio, Position, Trade
from app.schemas.portfolio import PortfolioSnapshot, PositionSnapshot
from app.services.market.hub import market_hub
from app.services.market.price_cache import price_cache


class PortfolioService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_portfolio_snapshot(self, portfolio_id: int = 1) -> PortfolioSnapshot:
        stmt = select(Portfolio).where(Portfolio.id == portfolio_id)
        res = await self.session.execute(stmt)
        portfolio = res.scalar_one_or_none()

        if not portfolio:
            raise ValueError("Portfolio not found")

        stmt_pos = select(Position).where(Position.portfolio_id == portfolio_id)
        res_pos = await self.session.execute(stmt_pos)
        positions_db = res_pos.scalars().all()

        positions = []
        total_market_value = Decimal(0)
        total_unrealized_pnl = Decimal(0)

        for pos in positions_db:
            quote = price_cache.get(pos.ticker)
            current_price = Decimal(str(quote.price)) if quote else pos.avg_cost

            market_value = current_price * Decimal(pos.quantity)
            cost_basis = pos.avg_cost * Decimal(pos.quantity)
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis * Decimal(100)) if cost_basis > 0 else Decimal(0)

            total_market_value += market_value
            total_unrealized_pnl += unrealized_pnl

            positions.append(PositionSnapshot(
                ticker=pos.ticker,
                quantity=pos.quantity,
                avg_cost=pos.avg_cost,
                current_price=current_price,
                market_value=market_value,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_pct=unrealized_pnl_pct
            ))

        equity = portfolio.cash + total_market_value
        unrealized_pnl_pct_total = (total_unrealized_pnl / (equity - total_unrealized_pnl) * Decimal(100)) if (equity - total_unrealized_pnl) > 0 else Decimal(0)

        return PortfolioSnapshot(
            cash=portfolio.cash,
            equity=equity,
            unrealized_pnl=total_unrealized_pnl,
            unrealized_pnl_pct=unrealized_pnl_pct_total,
            positions=positions
        )

    async def broadcast_portfolio(self, portfolio_id: int = 1) -> None:
        """Helper to get and broadcast the portfolio snapshot via SSE."""
        snap = await self.get_portfolio_snapshot(portfolio_id)
        await market_hub.broadcast("portfolio", snap.model_dump_json())

    async def reset_portfolio(self, portfolio_id: int = 1) -> None:
        """Reset the portfolio to initial cash and clear trades/positions."""
        from sqlalchemy import delete

        stmt = select(Portfolio).where(Portfolio.id == portfolio_id)
        res = await self.session.execute(stmt)
        portfolio = res.scalar_one()

        portfolio.cash = portfolio.starting_cash

        # Delete trades, positions, chat messages
        await self.session.execute(delete(Position).where(Position.portfolio_id == portfolio_id))
        await self.session.execute(delete(Trade).where(Trade.portfolio_id == portfolio_id))
        await self.session.execute(delete(ChatMessage).where(ChatMessage.portfolio_id == portfolio_id))

        await self.session.commit()
        await self.broadcast_portfolio(portfolio_id)
