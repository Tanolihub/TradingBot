import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.base import Base

# Setup an in-memory SQLite DB for testing
# Wait, SQLAlchemy async SQLite is supported.
engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    future=True
)
TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

@pytest_asyncio.fixture(autouse=True)
async def db_setup() -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session
from decimal import Decimal
from app.models.portfolio import Portfolio
import pytest_asyncio

@pytest_asyncio.fixture
async def setup_portfolio(db_session: AsyncSession) -> int:
    portfolio = Portfolio(id=1, cash=Decimal("10000.0000"), starting_cash=Decimal("10000.0000"))
    db_session.add(portfolio)
    await db_session.commit()
    return 1
