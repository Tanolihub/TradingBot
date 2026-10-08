from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Market data
    MARKET_DATA_PROVIDER: Literal["mock", "alpaca"] = "alpaca"
    ALPACA_API_KEY: str = ""
    ALPACA_API_SECRET: str = ""
    STALE_PRICE_SECONDS: int = 30

    # AI
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    COPILOT_MAX_TRADES_PER_REPLY: int = 5
    AI_AUTO_EXECUTE: bool = True

    # Trading
    STARTING_CASH: float = 10000.0

    # Web
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings(DATABASE_URL="") # type: ignore
