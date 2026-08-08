# ============================================================
# scoring.py
# ------------------------------------------------------------
# Binance Futures candidates ka technical + momentum score
# calculate karta hai.
#
# Score 0-100 ke beech hota hai.
# ============================================================

from binance_data import get_klines


# ============================================================
# SETTINGS
# ============================================================

TIMEFRAME = "15m"
KLINE_LIMIT = 100


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def calculate_ema(values, period):
    """Simple EMA calculate karta hai."""

    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    ema = sum(values[:period]) / period

    for price in values[period:]:
        ema = (
            (price - ema) * multiplier
        ) + ema

    return ema


def calculate_rsi(closes, period=14):
    """RSI calculate karta hai."""

    if len(closes) <= period:
        return None

    gains = []
    losses = []

    for i in range(1, len(closes)):

        change = closes[i] - closes[i - 1]

        if change > 0:
            gains.append(change)
            losses.append(0)

        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(
        gains[:period]
    ) / period

    avg_loss = sum(
        losses[:period]
    ) / period

    for i in range(period, len(gains)):

        avg_gain = (
            (avg_gain * (period - 1))
            + gains[i]
        ) / period

        avg_loss = (
            (avg_loss * (period - 1))
            + losses[i]
        ) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss

    return 100 - (
        100 / (1 + rs)
    )


def calculate_volume_ratio(volumes, period=20):
    """Current volume / average volume."""

    if len(volumes) < period + 1:
        return None

    current_volume = volumes[-1]

    previous_volumes = volumes[-period - 1:-1]

    average_volume = (
        sum(previous_volumes)
        / len(previous_volumes)
    )

    if average_volume <= 0:
        return None

    return current_volume / average_volume


# ============================================================
# SCORE SYMBOL
# ============================================================

def score_symbol(
    symbol,
    last_price,
    change_pct,
    quote_volume,
    trade_count,
):
    """
    Ek Binance Futures symbol ka detailed score calculate karta hai.

    Maximum score = 100
    """

    # --------------------------------------------------------
    # Historical candles
    # --------------------------------------------------------

    df = get_klines(
        symbol=symbol,
        interval=TIMEFRAME,
        limit=KLINE_LIMIT,
    )

    if df.empty:

        return {
            "symbol": symbol,
            "score": 0,
            "direction": "NEUTRAL",
            "reason": "No candle data",
        }

    if len(df) < 50:

        return {
            "symbol": symbol,
            "score": 0,
            "direction": "NEUTRAL",
            "reason": "Insufficient candle data",
        }

    # --------------------------------------------------------
    # Data
    # --------------------------------------------------------

    closes = df["close"].tolist()

    volumes = df["volume"].tolist()

    current_price = closes[-1]

    # --------------------------------------------------------
    # EMA
    # --------------------------------------------------------

    ema20 = calculate_ema(
        closes,
        20
    )

    ema50 = calculate_ema(
        closes,
        50
    )

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    rsi = calculate_rsi(
        closes,
        14
    )

    # --------------------------------------------------------
    # Volume ratio
    # --------------------------------------------------------

    volume_ratio = calculate_volume_ratio(
        volumes,
        20
    )

    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    score = 0

    bullish_points = 0
    bearish_points = 0

    reasons = []

    # ========================================================
    # 1. EMA TREND
    # ========================================================

    if ema20 is not None and ema50 is not None:

        if current_price > ema20 > ema50:

            score += 25
            bullish_points += 25

            reasons.append(
                "Price > EMA20 > EMA50"
            )

        elif current_price < ema20 < ema50:

            score += 25
            bearish_points += 25

            reasons.append(
                "Price < EMA20 < EMA50"
            )

        elif current_price > ema20:

            score += 12
            bullish_points += 12

            reasons.append(
                "Price above EMA20"
            )

        elif current_price < ema20:

            score += 12
            bearish_points += 12

            reasons.append(
                "Price below EMA20"
            )

    # ========================================================
    # 2. RSI MOMENTUM
    # ========================================================

    if rsi is not None:

        if 55 <= rsi <= 70:

            score += 20
            bullish_points += 20

            reasons.append(
                f"RSI bullish ({rsi:.1f})"
            )

        elif 30 <= rsi <= 45:

            score += 20
            bearish_points += 20

            reasons.append(
                f"RSI bearish ({rsi:.1f})"
            )

        elif 50 < rsi < 55:

            score += 8

        elif 45 < rsi <= 50:

            score += 8

    # ========================================================
    # 3. PRICE MOMENTUM
    # ========================================================

    if change_pct >= 5:

        score += 20
        bullish_points += 20

        reasons.append(
            f"Strong bullish momentum ({change_pct:.2f}%)"
        )

    elif change_pct >= 2:

        score += 12
        bullish_points += 12

        reasons.append(
            f"Bullish momentum ({change_pct:.2f}%)"
        )

    elif change_pct <= -5:

        score += 20
        bearish_points += 20

        reasons.append(
            f"Strong bearish momentum ({change_pct:.2f}%)"
        )

    elif change_pct <= -2:

        score += 12
        bearish_points += 12

        reasons.append(
            f"Bearish momentum ({change_pct:.2f}%)"
        )

    # ========================================================
    # 4. VOLUME
    # ========================================================

    if volume_ratio is not None:

        if volume_ratio >= 3:

            score += 20

            if bullish_points >= bearish_points:
                bullish_points += 20
            else:
                bearish_points += 20

            reasons.append(
                f"Volume spike {volume_ratio:.1f}x"
            )

        elif volume_ratio >= 2:

            score += 15

            if bullish_points >= bearish_points:
                bullish_points += 15
            else:
                bearish_points += 15

            reasons.append(
                f"High volume {volume_ratio:.1f}x"
            )

        elif volume_ratio >= 1.3:

            score += 8

            if bullish_points >= bearish_points:
                bullish_points += 8
            else:
                bearish_points += 8

    # ========================================================
    # 5. MARKET ACTIVITY
    # ========================================================

    if quote_volume >= 50_000_000:

        score += 15

        reasons.append(
            "Very high 24H volume"
        )

    elif quote_volume >= 10_000_000:

        score += 10

        reasons.append(
            "High 24H volume"
        )

    elif quote_volume >= 1_000_000:

        score += 5

    # ========================================================
    # FINAL SCORE LIMIT
    # ========================================================

    if score > 100:
        score = 100

    # ========================================================
    # DIRECTION
    # ========================================================

    if bullish_points > bearish_points:

        direction = "LONG"

    elif bearish_points > bullish_points:

        direction = "SHORT"

    else:

        direction = "NEUTRAL"

    # ========================================================
    # SIGNAL QUALITY
    # ========================================================

    if score >= 80:

        quality = "VERY STRONG"

    elif score >= 70:

        quality = "STRONG"

    elif score >= 60:

        quality = "GOOD"

    elif score >= 50:

        quality = "WATCH"

    else:

        quality = "WEAK"

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {
        "symbol": symbol,

        "score": round(
            score,
            2
        ),

        "direction": direction,

        "quality": quality,

        "price": current_price,

        "change_pct": change_pct,

        "quote_volume": quote_volume,

        "trade_count": trade_count,

        "ema20": ema20,

        "ema50": ema50,

        "rsi": rsi,

        "volume_ratio": volume_ratio,

        "reason": reasons,
    }
