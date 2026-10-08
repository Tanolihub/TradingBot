from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.portfolio import PortfolioSnapshot
from app.services.portfolio import PortfolioService

router = APIRouter()

@router.get("/api/portfolio", response_model=PortfolioSnapshot)
async def get_portfolio(db: Annotated[AsyncSession, Depends(get_db)]) -> PortfolioSnapshot:
    svc = PortfolioService(db)
    return await svc.get_portfolio_snapshot(portfolio_id=1)

@router.post("/api/portfolio/reset")
async def reset_portfolio(db: Annotated[AsyncSession, Depends(get_db)]) -> dict[str, str]:
    svc = PortfolioService(db)
    await svc.reset_portfolio(portfolio_id=1)
    return {"status": "ok"}
