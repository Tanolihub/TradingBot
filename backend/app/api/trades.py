
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.portfolio import Trade
from app.schemas.portfolio import TradeRequest, TradeResult
from app.services.trading import TradingEngine

router = APIRouter()

@router.post("/api/trades", response_model=TradeResult)
async def create_trade(req: TradeRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> TradeResult:
    engine = TradingEngine(db)
    return await engine.execute_market_order(
        portfolio_id=1,
        ticker=req.ticker.upper(),
        side=req.side,
        quantity=req.quantity,
        source="manual",
        idempotency_key=req.idempotency_key
    )

@router.get("/api/trades", response_model=list[TradeResult])
async def get_trades(limit: int = 50, cursor: int | None = None, db: Annotated[AsyncSession, Depends(get_db)] = None): # type: ignore
    # Note: cursor here could be offset or pagination. For simplicity, we just order by time desc and use limit.
    # UUID doesn't sequence easily, we can order by executed_at
    stmt = select(Trade).where(Trade.portfolio_id == 1).order_by(Trade.executed_at.desc()).limit(limit)
    res = await db.execute(stmt)
    trades_db = res.scalars().all()

    return [
        TradeResult(
            id=t.id,
            ticker=t.ticker,
            side=t.side,
            quantity=t.quantity,
            price=t.price,
            notional=t.notional,
            realized_pnl=t.realized_pnl,
            executed_at=t.executed_at,
            source=t.source
        )
        for t in trades_db
    ]
