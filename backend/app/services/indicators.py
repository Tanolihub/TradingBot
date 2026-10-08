from typing import Any

import numpy as np
import pandas as pd


def calc_sma(series: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    return series.rolling(window=period, min_periods=period).mean()

def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI using Wilder's Smoothing, exactly matching TA-Lib."""
    prices = series.values
    if len(prices) < period + 1:
        return pd.Series(np.nan, index=series.index)

    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = np.full_like(prices, np.nan, dtype=float)
    avg_loss = np.full_like(prices, np.nan, dtype=float)
    rsi = np.full_like(prices, np.nan, dtype=float)

    avg_gain[period] = np.mean(gains[:period])
    avg_loss[period] = np.mean(losses[:period])

    # Calculate rs for the first period
    if avg_loss[period] == 0:
        rsi[period] = 100.0
    else:
        rs = avg_gain[period] / avg_loss[period]
        rsi[period] = 100.0 - (100.0 / (1.0 + rs))

    for i in range(period + 1, len(prices)):
        avg_gain[i] = (avg_gain[i-1] * (period - 1) + gains[i-1]) / period
        avg_loss[i] = (avg_loss[i-1] * (period - 1) + losses[i-1]) / period

        if avg_loss[i] == 0:
            rsi[i] = 100.0
        else:
            rs = avg_gain[i] / avg_loss[i]
            rsi[i] = 100.0 - (100.0 / (1.0 + rs))

    return pd.Series(rsi, index=series.index)

def calc_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD, Signal, and Histogram."""
    # TA-Lib MACD uses EMA
    ema_fast = series.ewm(span=fast, adjust=False, min_periods=fast).mean()
    ema_slow = series.ewm(span=slow, adjust=False, min_periods=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def get_signal_labels(
    price: float,
    sma20: float | None,
    sma50: float | None,
    rsi: float | None,
    macd: float | None,
    macd_sig: float | None,
    macd_hist: float | None
) -> dict[str, str]:
    """Pre-label signals for LLM."""
    labels = {
        "trend": "unknown",
        "rsi_zone": "neutral",
        "macd_cross": "none"
    }

    # Trend
    if sma20 is not None and sma50 is not None and not np.isnan(sma20) and not np.isnan(sma50):
        if price > sma20 and price > sma50:
            labels["trend"] = "above_sma20_and_sma50"
        elif price < sma20 and price < sma50:
            labels["trend"] = "below_sma20_and_sma50"
        elif price > sma20 and price < sma50:
            labels["trend"] = "above_sma20_below_sma50"
        elif price < sma20 and price > sma50:
            labels["trend"] = "below_sma20_above_sma50"

    # RSI Zone
    if rsi is not None and not np.isnan(rsi):
        if rsi >= 70:
            labels["rsi_zone"] = "overbought"
        elif rsi <= 30:
            labels["rsi_zone"] = "oversold"

    # MACD Cross (naive, based on current state rather than crossover event)
    # A true cross would require looking at the previous bar, but we can
    # label the current regime (bullish/bearish) or recent cross if hist is small.
    if macd is not None and macd_sig is not None and not np.isnan(macd) and not np.isnan(macd_sig):
        if macd > macd_sig:
            labels["macd_cross"] = "bullish"
        elif macd < macd_sig:
            labels["macd_cross"] = "bearish"

    return labels

def _to_float_or_null(val: Any) -> float | None:
    if pd.isna(val):
        return None
    return float(val)

class IndicatorService:
    def __init__(self, market_provider: Any):
        self.market_provider = market_provider
        self._cache: dict[str, dict[str, Any]] = {}

    async def get_indicators(self, ticker: str, timeframe: str = "1D") -> dict[str, Any]:
        import time

        from app.services.market.price_cache import price_cache

        cache_key = f"{ticker}_{timeframe}"
        now = time.time()

        # Throttled recompute: return cached if < 5s old
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if now - entry["ts"] < 5.0:
                return entry["data"]  # type: ignore

        # Fetch bars (lookback 200)
        bars = await self.market_provider.get_bars(ticker, timeframe, limit=200)
        if not bars:
            return {"error": "no data"}

        # Patch with live price if available
        live_quote = price_cache.get(ticker)

        closes = [b.close for b in bars]
        # Replace last close with live price to get live indicator value
        if live_quote and closes:
            closes[-1] = live_quote.price

        series = pd.Series(closes)

        sma20 = calc_sma(series, 20)
        sma50 = calc_sma(series, 50)
        rsi = calc_rsi(series, 14)
        macd_line, signal_line, hist = calc_macd(series)

        latest_price = float(closes[-1]) if closes else 0.0
        latest_sma20 = _to_float_or_null(sma20.iloc[-1]) if len(sma20) else None
        latest_sma50 = _to_float_or_null(sma50.iloc[-1]) if len(sma50) else None
        latest_rsi = _to_float_or_null(rsi.iloc[-1]) if len(rsi) else None
        latest_macd = _to_float_or_null(macd_line.iloc[-1]) if len(macd_line) else None
        latest_macd_sig = _to_float_or_null(signal_line.iloc[-1]) if len(signal_line) else None
        latest_macd_hist = _to_float_or_null(hist.iloc[-1]) if len(hist) else None

        labels = get_signal_labels(
            latest_price, latest_sma20, latest_sma50, latest_rsi, latest_macd, latest_macd_sig, latest_macd_hist
        )

        data = {
            "price": latest_price,
            "sma20": latest_sma20,
            "sma50": latest_sma50,
            "rsi": latest_rsi,
            "macd": latest_macd,
            "macd_sig": latest_macd_sig,
            "macd_hist": latest_macd_hist,
            "labels": labels
        }

        self._cache[cache_key] = {
            "ts": now,
            "data": data
        }
        return data
