# ============================================================
# scoring.py - SCORE AUR RATING CALCULATION
# ------------------------------------------------------------
# Ye file decide karti hai kaun-sa coin "movement" ke liye ready hai.
# Hum 4 cheezein mila ke ek 0-100 score banate hain:
#   1. 24h volume kitna hai aur kitna trade ho raha hai
#   2. Pichle 15-minute candles me price kitna hil rahi hai
#   3. RSI (Relative Strength Index) - overbought / oversold
#   4. Volatility (candles ka high-low range)
# Score ke basis pe A / B / C rating di jaati hai.
# ============================================================

import pandas as pd
import numpy as np
from binance_data import get_klines


# ---------- Helper functions (indicators) ----------

def compute_rsi(closes, period=14):
    """
    RSI - Relative Strength Index nikalta hai.
    > 70 = overbought (zyada kharida gaya, girne ka risk)
    < 30 = oversold (zyada becha gaya, uthne ka chance)
    30-70 ke beech = neutral / calm
    """
    closes = pd.Series(closes).astype(float)
    delta = closes.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50).iloc[-1]


def compute_volatility_pct(df):
    """
    Pichle candles ka average (high-low)/close ratio (%).
    Zyada value = zyada price movement / volatility.
    """
    if df.empty:
        return 0.0
    rng = (df["high"] - df["low"]) / df["close"]
    return float(rng.mean() * 100)


def compute_relative_volume(df, window=20):
    """
    Last candle ka volume vs pichle 'window' candles ka avg volume.
    > 1.5 matlab aaj/aise volume spike hai - market me entry ho rahi hai.
    """
    if df.empty or len(df) < 5:
        return 0.0
    vols = df["volume"].astype(float).values
    if len(vols) < window:
        base = vols[:-1].mean()
    else:
        base = vols[-(window+1):-1].mean()
    if base == 0:
        return 0.0
    return float(vols[-1] / base)


# ---------- Main scoring function ----------

def score_symbol(symbol, last_price, change_pct, quote_volume, trade_count):
    """
    Ek symbol ke liye 0-100 score aur A/B/C rating nikalta hai.
    Returns: dict with score, rating, reason, sub_scores
    """
    # 1) Volume sub-score (max 30)
    # 50M USDT volume good, 500M+ excellent
    vol_score = min(30.0, np.log10(max(quote_volume, 1)) * 6)

    # 2) Trade count sub-score (max 15)
    # Zyada trades = zyada active
    trade_score = min(15.0, np.log10(max(trade_count, 1)) * 3)

    # 3) Recent 15m change sub-score (max 15)
    # Strong positive move (mild) = bullish, very big move = risky
    abs_change = abs(change_pct)
    if change_pct > 0:
        chg_score = min(15.0, abs_change * 1.5)
    else:
        chg_score = min(15.0, abs_change * 0.7)  # bade drop ko thoda kam score

    # 4) Candle-based indicators (klines se)
    df = get_klines(symbol, interval="15m")
    if df.empty or len(df) < 10:
        return {
            "symbol": symbol,
            "score": 0.0,
            "rating": "C",
            "reason": "data-not-enough",
            "sub_scores": {"volume": vol_score, "trade": trade_score, "change": chg_score},
        }

    rsi = compute_rsi(df["close"])
    vol15 = compute_volatility_pct(df)
    rel_vol = compute_relative_volume(df)

    # 5) RSI sub-score (max 20)
    # RSI 50-65 = best (trend building), 30-50 = oversold bounce, 70+ = risky
    if 50 <= rsi <= 65:
        rsi_score = 20.0
    elif 30 <= rsi < 50:
        rsi_score = 16.0
    elif 65 < rsi <= 75:
        rsi_score = 12.0
    elif 75 < rsi:
        rsi_score = 5.0
    else:  # < 30
        rsi_score = 14.0

    # 6) Volatility sub-score (max 10)
    # Thodi-volatility healthy; 0% flat boring; bahut zyada = risky
    if 0.5 <= vol15 <= 3.0:
        vol_sub = 10.0
    elif vol15 < 0.5:
        vol_sub = 3.0
    elif 3.0 < vol15 <= 6.0:
        vol_sub = 7.0
    else:
        vol_sub = 4.0

    # 7) Relative volume spike sub-score (max 10)
    if rel_vol >= 2.5:
        spike_score = 10.0
    elif rel_vol >= 1.5:
        spike_score = 7.0
    elif rel_vol >= 1.1:
        spike_score = 4.0
    else:
        spike_score = 1.0

    total = vol_score + trade_score + chg_score + rsi_score + vol_sub + spike_score
    total = min(100.0, total)

    # ---- Rating bucket ----
    if total >= 75:
        rating = "A"
    elif total >= 55:
        rating = "B"
    else:
        rating = "C"

    # ek chhoti si readable reason
    if rel_vol >= 2.0:
        rsn = "volume-spike"
    elif rsi < 30:
        rsn = "oversold-rebound"
    elif rsi > 70:
        rsn = "overbought-risky"
    elif 50 <= rsi <= 65 and vol15 >= 1.0:
        rsn = "building-trend"
    else:
        rsn = "active-mover"

    return {
        "symbol": symbol,
        "score": round(total, 2),
        "rating": rating,
        "reason": rsn,
        "rsi": round(rsi, 1),
        "vol15_pct": round(vol15, 2),
        "rel_volume": round(rel_vol, 2),
        "sub_scores": {
            "volume": round(vol_score, 1),
            "trade": round(trade_score, 1),
            "change": round(chg_score, 1),
            "rsi": round(rsi_score, 1),
            "volatility": round(vol_sub, 1),
            "spike": round(spike_score, 1),
        },
    }


def rate_to_emoji(rating):
    return {"A": "🟢", "B": "🟡", "C": "🔴"}.get(rating, "⚪")
