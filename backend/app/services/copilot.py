import json
import logging
from typing import Any

from groq import AsyncGroq
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.portfolio import ChatMessage
from app.schemas.chat import AiResponse, TradeReport
from app.services.market.base import MarketProvider
from app.services.market.hub import market_hub
from app.services.market.price_cache import price_cache
from app.services.portfolio import PortfolioService
from app.services.trading import TradingEngine

logger = logging.getLogger(__name__)

class CopilotService:
    def __init__(self, session: AsyncSession, provider: MarketProvider):
        self.session = session
        self.provider = provider
        self.portfolio_svc = PortfolioService(session)
        self.trading_engine = TradingEngine(session)
        self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None

    async def build_context(self, portfolio_id: int) -> dict[str, Any]:
        snap = await self.portfolio_svc.get_portfolio_snapshot(portfolio_id)
        from app.services.indicators import IndicatorService
        ind_svc = IndicatorService(self.provider)

        from app.services.trading import ALLOWED_TICKERS
        
        quotes_and_signals = {}
        for ticker in ALLOWED_TICKERS:
            q = price_cache.get(ticker)
            if q:
                # Get history to grab last indicator values
                try:
                    inds = await ind_svc.get_indicators(ticker, "1Min")
                    quotes_and_signals[ticker] = {
                        "price": float(q.price),
                        "change_pct": float(q.change_pct),
                        "sma_20": inds.get("sma20"),
                        "rsi": inds.get("rsi")
                    }
                except Exception:
                    quotes_and_signals[ticker] = {
                        "price": float(q.price),
                        "change_pct": float(q.change_pct)
                    }

        context = {
            "market_status": market_hub.market_status.market,
            "cash": float(snap.cash),
            "portfolio": [
                {
                    "ticker": p.ticker,
                    "qty": p.quantity,
                    "unrealized_pnl_pct": float(p.unrealized_pnl_pct),
                    "market_value": float(p.market_value)
                } for p in snap.positions
            ],
            "quotes_and_signals": quotes_and_signals,
            "rules": [
                f"You can execute up to {settings.COPILOT_MAX_TRADES_PER_REPLY} trades.",
                "Do not hallucinate tickers.",
                "Respond matching the strictly validated JSON schema: { \"reply\": \"str\", \"trades\": [ {\"ticker\": \"str\", \"side\": \"buy|sell\", \"quantity\": int, \"reasoning\": \"str\"} ] }",
                "Ensure quantity is a positive integer.",
                "Return ONLY a JSON object and no markdown blocks."
            ]
        }
        return context

    async def process_chat(self, portfolio_id: int, message: str) -> tuple[str, list[TradeReport]]:
        if not self.groq_client:
            return "AI copilot is disabled (missing GROQ_API_KEY).", []

        # 1. Build context
        context = await self.build_context(portfolio_id)

        system_prompt = f"""You are NeonPulse AI, an advanced simulated trading copilot.
You have the ability to execute trades on behalf of the user.
Here is the current state of the market and portfolio:
{json.dumps(context, indent=2)}

You must respond in pure JSON matching this schema:
{{
  "reply": "Conversational reply to the user explaining your actions.",
  "trades": [
    {{
      "ticker": "AAPL",
      "side": "buy" or "sell",
      "quantity": 10,
      "reasoning": "Brief reason"
    }}
  ]
}}
If no trades are needed, return an empty trades array.
Output ONLY JSON, no markdown formatting.
"""

        # 2. Call Groq
        try:
            completion = await self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                model=settings.GROQ_MODEL,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            raw_response = completion.choices[0].message.content or "{}"
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return "Failed to connect to AI brain.", []

        # 3. Parse and Validate
        try:
            parsed = json.loads(raw_response)
            ai_resp = AiResponse(**parsed)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Invalid AI output: {raw_response} - Error: {e}")
            return "I generated an invalid response and could not process your request safely.", []

        if len(ai_resp.trades) > settings.COPILOT_MAX_TRADES_PER_REPLY:
            ai_resp.trades = ai_resp.trades[:settings.COPILOT_MAX_TRADES_PER_REPLY]

        # 4. Save User Message
        user_msg = ChatMessage(portfolio_id=portfolio_id, role="user", content=message)
        self.session.add(user_msg)
        await self.session.commit()

        # 5. Execute Trades
        reports = []
        if settings.AI_AUTO_EXECUTE:
            for t in ai_resp.trades:
                try:
                    await self.trading_engine.execute_market_order(
                        portfolio_id=portfolio_id,
                        ticker=t.ticker.upper(),
                        side=t.side,
                        quantity=t.quantity,
                        source="ai",
                        chat_message_id=user_msg.id
                    )
                    reports.append(TradeReport(
                        ticker=t.ticker.upper(),
                        side=t.side,
                        quantity=t.quantity,
                        status="success"
                    ))
                except Exception as e:
                    reports.append(TradeReport(
                        ticker=t.ticker.upper(),
                        side=t.side,
                        quantity=t.quantity,
                        status="failed",
                        detail=str(e)
                    ))

        # 6. Save AI Reply
        ai_msg = ChatMessage(
            portfolio_id=portfolio_id,
            role="assistant",
            content=ai_resp.reply,
            payload={"reports": [r.model_dump() for r in reports]}
        )
        self.session.add(ai_msg)
        await self.session.commit()

        # Broadcast portfolio update if trades occurred
        if any(r.status == 'success' for r in reports):
            await self.portfolio_svc.broadcast_portfolio(portfolio_id)

        return ai_resp.reply, reports
