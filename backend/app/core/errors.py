
from fastapi import HTTPException


class TradingError(HTTPException):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(
            status_code=422,
            detail={"code": code, "message": message}
        )

# Predefined errors
def err_price_unavailable(ticker: str) -> TradingError:
    return TradingError("PRICE_UNAVAILABLE", f"Price unavailable for {ticker}")

def err_insufficient_funds(cash: float, cost: float) -> TradingError:
    return TradingError("INSUFFICIENT_FUNDS", f"Insufficient funds: need {cost}, have {cash}")

def err_insufficient_shares(ticker: str, have: int, need: int) -> TradingError:
    return TradingError("INSUFFICIENT_SHARES", f"Insufficient shares of {ticker}: have {have}, need {need}")

def err_unknown_ticker(ticker: str) -> TradingError:
    return TradingError("UNKNOWN_TICKER", f"Unknown ticker: {ticker}")
