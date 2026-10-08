import pytest
from unittest.mock import patch, MagicMock
from app.services.copilot import CopilotService
from decimal import Decimal

@pytest.mark.asyncio
async def test_copilot_disabled_no_key(db_session, setup_portfolio):
    from app.core.config import settings
    # Override key
    settings.GROQ_API_KEY = ""
    # Provider mock
    provider = MagicMock()

    svc = CopilotService(db_session, provider)
    reply, reports = await svc.process_chat(1, "buy 5 aapl")

    assert "disabled" in reply
    assert len(reports) == 0

@pytest.mark.asyncio
async def test_copilot_executes_trades(db_session, setup_portfolio):
    from app.core.config import settings
    settings.GROQ_API_KEY = "dummy"
    settings.AI_AUTO_EXECUTE = True

    provider = MagicMock()
    svc = CopilotService(db_session, provider)

    # Mock groq completion
    mock_resp = {
        "reply": "Sure, buying 5 AAPL.",
        "trades": [
            {"ticker": "AAPL", "side": "buy", "quantity": 5, "reasoning": "Test"}
        ]
    }

    with patch.object(svc.groq_client.chat.completions, 'create') as mock_create:
        mock_choice = MagicMock()
        mock_choice.message.content = __import__('json').dumps(mock_resp)
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        mock_create.return_value = mock_completion

        from app.services.market.price_cache import price_cache
        from app.schemas.market import QuoteSnapshot
        from datetime import datetime, timezone
        price_cache.update("AAPL", QuoteSnapshot(ticker="AAPL", price=Decimal("150.00"), change=Decimal("1.0"), change_pct=Decimal("0.5"), ts=datetime.now(timezone.utc)))

        reply, reports = await svc.process_chat(1, "buy 5 AAPL")

        assert reply == "Sure, buying 5 AAPL."
        assert len(reports) == 1
        assert reports[0].status == "success"
        assert reports[0].ticker == "AAPL"
