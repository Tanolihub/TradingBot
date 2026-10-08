import pytest
from datetime import datetime, timezone
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.trading import TradingEngine
from app.services.portfolio import PortfolioService
from app.core.errors import TradingError
from app.schemas.market import QuoteSnapshot
from app.services.market.price_cache import price_cache



@pytest.mark.asyncio
async def test_successful_buy(db_session: AsyncSession, setup_portfolio: int):
    # Setup mock price
    price_cache.update("AAPL", QuoteSnapshot(price=150.0, change=0.0, change_pct=0.0, ts=datetime.now(timezone.utc)))

    engine = TradingEngine(db_session)
    res = await engine.execute_market_order(
        portfolio_id=setup_portfolio,
        ticker="AAPL",
        side="buy",
        quantity=10,
        source="manual"
    )

    assert res.ticker == "AAPL"
    assert res.quantity == 10
    assert res.price == Decimal("150.0")
    assert res.notional == Decimal("1500.0")
    assert res.side == "buy"

    # Check portfolio cash decreased
    portfolio_svc = PortfolioService(db_session)
    snap = await portfolio_svc.get_portfolio_snapshot(setup_portfolio)
    assert snap.cash == Decimal("8500.0")

    # Check position created
    assert len(snap.positions) == 1
    assert snap.positions[0].ticker == "AAPL"
    assert snap.positions[0].quantity == 10
    assert snap.positions[0].avg_cost == Decimal("150.0")

@pytest.mark.asyncio
async def test_insufficient_funds(db_session: AsyncSession, setup_portfolio: int):
    price_cache.update("AAPL", QuoteSnapshot(price=150.0, change=0.0, change_pct=0.0, ts=datetime.now(timezone.utc)))
    engine = TradingEngine(db_session)

    with pytest.raises(TradingError) as exc:
        await engine.execute_market_order(
            portfolio_id=setup_portfolio,
            ticker="AAPL",
            side="buy",
            quantity=100,  # 100 * 150 = 15000 > 10000
            source="manual"
        )
    assert exc.value.detail["code"] == "INSUFFICIENT_FUNDS"

@pytest.mark.asyncio
async def test_successful_sell_and_pnl(db_session: AsyncSession, setup_portfolio: int):
    price_cache.update("AAPL", QuoteSnapshot(price=150.0, change=0.0, change_pct=0.0, ts=datetime.now(timezone.utc)))
    engine = TradingEngine(db_session)

    # Buy 10 AAPL @ 150
    await engine.execute_market_order(setup_portfolio, "AAPL", "buy", 10, "manual")

    # Price goes to 160
    price_cache.update("AAPL", QuoteSnapshot(price=160.0, change=10.0, change_pct=6.66, ts=datetime.now(timezone.utc)))

    # Sell 5 AAPL @ 160
    res = await engine.execute_market_order(setup_portfolio, "AAPL", "sell", 5, "manual")
    assert res.realized_pnl == Decimal("50.0")  # 5 * (160 - 150)

    portfolio_svc = PortfolioService(db_session)
    snap = await portfolio_svc.get_portfolio_snapshot(setup_portfolio)
    assert snap.cash == Decimal("8500.0") + Decimal("800.0")  # 9300

    # Remaining position is 5 AAPL @ 150
    assert len(snap.positions) == 1
    assert snap.positions[0].quantity == 5
    assert snap.positions[0].avg_cost == Decimal("150.0")

    # Check unrealized PnL of remaining
    # Market value = 5 * 160 = 800, cost = 750, unrealized = 50
    assert snap.positions[0].unrealized_pnl == Decimal("50.0")

    # Sell remaining 5 AAPL @ 160
    await engine.execute_market_order(setup_portfolio, "AAPL", "sell", 5, "manual")

    snap2 = await portfolio_svc.get_portfolio_snapshot(setup_portfolio)
    assert snap2.cash == Decimal("10100.0")
    assert len(snap2.positions) == 0

@pytest.mark.asyncio
async def test_short_selling_rejected(db_session: AsyncSession, setup_portfolio: int):
    price_cache.update("AAPL", QuoteSnapshot(price=150.0, change=0.0, change_pct=0.0, ts=datetime.now(timezone.utc)))
    engine = TradingEngine(db_session)

    with pytest.raises(TradingError) as exc:
        await engine.execute_market_order(setup_portfolio, "AAPL", "sell", 5, "manual")
    assert exc.value.detail["code"] == "INSUFFICIENT_SHARES"

@pytest.mark.asyncio
async def test_idempotency(db_session: AsyncSession, setup_portfolio: int):
    price_cache.update("AAPL", QuoteSnapshot(price=150.0, change=0.0, change_pct=0.0, ts=datetime.now(timezone.utc)))
    engine = TradingEngine(db_session)

    ik = str(uuid.uuid4())
    res1 = await engine.execute_market_order(setup_portfolio, "AAPL", "buy", 5, "manual", idempotency_key=ik)
    res2 = await engine.execute_market_order(setup_portfolio, "AAPL", "buy", 5, "manual", idempotency_key=ik)

    assert res1.id == res2.id

    portfolio_svc = PortfolioService(db_session)
    snap = await portfolio_svc.get_portfolio_snapshot(setup_portfolio)
    assert snap.positions[0].quantity == 5  # Only 5 bought, not 10
