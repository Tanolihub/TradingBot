import pandas as pd
import numpy as np
from app.services.indicators import calc_sma, calc_rsi, calc_macd, get_signal_labels

def test_sma():
    series = pd.Series([10.0, 11.0, 12.0, 13.0, 14.0])

    # window=3
    sma3 = calc_sma(series, 3)

    assert pd.isna(sma3.iloc[0])
    assert pd.isna(sma3.iloc[1])
    assert sma3.iloc[2] == 11.0  # (10+11+12)/3
    assert sma3.iloc[3] == 12.0
    assert sma3.iloc[4] == 13.0

def test_rsi_constant_up():
    series = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25])
    rsi = calc_rsi(series, 14)
    # Since it goes up every time, RSI should be 100 once we hit period (14th element which is index 14)
    assert pd.isna(rsi.iloc[13])
    assert rsi.iloc[14] == 100.0

def test_macd():
    np.random.seed(42)
    # Random walk
    series = pd.Series(100 + np.random.randn(50).cumsum())
    macd, sig, hist = calc_macd(series)

    # MACD fast=12, slow=26, sig=9
    # Initial NaN periods
    assert pd.isna(macd.iloc[24])
    assert not pd.isna(macd.iloc[25])

    assert pd.isna(sig.iloc[32])
    assert not pd.isna(sig.iloc[33])

    assert pd.isna(hist.iloc[32])
    assert not pd.isna(hist.iloc[33])

def test_signal_labels():
    labels = get_signal_labels(
        price=150.0,
        sma20=140.0,
        sma50=130.0,
        rsi=75.0,
        macd=1.5,
        macd_sig=1.0,
        macd_hist=0.5
    )
    assert labels["trend"] == "above_sma20_and_sma50"
    assert labels["rsi_zone"] == "overbought"
    assert labels["macd_cross"] == "bullish"

    labels_bearish = get_signal_labels(
        price=120.0,
        sma20=130.0,
        sma50=140.0,
        rsi=25.0,
        macd=-1.5,
        macd_sig=-1.0,
        macd_hist=-0.5
    )
    assert labels_bearish["trend"] == "below_sma20_and_sma50"
    assert labels_bearish["rsi_zone"] == "oversold"
    assert labels_bearish["macd_cross"] == "bearish"
