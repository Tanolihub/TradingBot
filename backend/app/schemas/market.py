from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Bar(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class Tick(BaseModel):
    ticker: str
    price: float
    change: float
    change_pct: float
    ts: datetime

class MarketStatus(BaseModel):
    market: Literal["open", "closed", "delayed", "feed_down"]
    feed: Literal["connected", "reconnecting", "down"]

class QuoteSnapshot(BaseModel):
    price: float
    change: float
    change_pct: float
    ts: datetime
