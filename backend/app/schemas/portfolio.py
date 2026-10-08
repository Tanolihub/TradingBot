from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PositionSnapshot(BaseModel):
    ticker: str
    quantity: int
    avg_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal

class PortfolioSnapshot(BaseModel):
    cash: Decimal
    equity: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal
    positions: list[PositionSnapshot]

class TradeRequest(BaseModel):
    ticker: str = Field(pattern=r"^[A-Z.]{1,6}$")
    side: str
    quantity: int
    idempotency_key: str | None = None

class TradeResult(BaseModel):
    id: UUID
    ticker: str
    side: str
    quantity: int
    price: Decimal
    notional: Decimal
    realized_pnl: Decimal | None
    executed_at: datetime
    source: str
