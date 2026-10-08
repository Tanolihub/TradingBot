from typing import Literal

from pydantic import BaseModel, Field


class AiTradeAction(BaseModel):
    ticker: str = Field(..., description="The ticker symbol to trade")
    side: Literal["buy", "sell"] = Field(..., description="Trade side, must be 'buy' or 'sell'")
    quantity: int = Field(..., description="Number of shares to trade, must be positive integer")
    reasoning: str = Field(..., description="Brief reasoning for this trade")

class AiResponse(BaseModel):
    reply: str = Field(..., description="The conversational reply to the user")
    trades: list[AiTradeAction] = Field(default_factory=list, description="List of trades to execute")

class ChatRequest(BaseModel):
    message: str

class TradeReport(BaseModel):
    ticker: str
    side: str
    quantity: int
    status: Literal["success", "failed"]
    detail: str | None = None

class ChatResponse(BaseModel):
    reply: str
    reports: list[TradeReport]
