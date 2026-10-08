from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models.portfolio import ChatMessage
from app.schemas.chat import ChatRequest, ChatResponse
from app.api.deps import get_market_provider
from app.services.market.base import MarketProvider
from app.services.copilot import CopilotService

router = APIRouter()

@router.post("/api/chat", response_model=ChatResponse)
async def chat_with_copilot(
    req: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    provider: Annotated[MarketProvider, Depends(get_market_provider)]
) -> ChatResponse:
    svc = CopilotService(db, provider)
    reply, reports = await svc.process_chat(portfolio_id=1, message=req.message)
    return ChatResponse(reply=reply, reports=reports)

@router.get("/api/chat/history")
async def get_chat_history(db: Annotated[AsyncSession, Depends(get_db)], limit: int = 50) -> list[dict[str, Any]]:
    stmt = select(ChatMessage).where(ChatMessage.portfolio_id == 1).order_by(ChatMessage.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    messages = res.scalars().all()

    # Return chronologically
    return [
        {
            "role": m.role,
            "content": m.content,
            "payload": m.payload
        }
        for m in reversed(messages)
    ]
