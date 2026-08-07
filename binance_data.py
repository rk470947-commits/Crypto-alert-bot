# ============================================================
# binance_data.py - BINANCE SE DATA LANA
# ------------------------------------------------------------
# Ye file Binance ki public API se:
#   1. Saari USDT trading pairs ki list laati hai
#   2. Sabka 24hr ticker data laati hai (volume, price change)
#   3. Top candidates ke liye 15-min candles laati hai
# ============================================================

import requests
import time
import pandas as pd
from config import BINANCE_BASE_URL, KLINE_LIMIT


def _get(url, params=None, retries=3):
    """Request bhejta hai aur agar fail ho to dobara try karta hai."""
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"[warn] API call fail (try {attempt+1}/{retries}): {e}")
            time.sleep(2)
    return None


def get_usdt_symbols():
    """
    Saari USDT trading pairs ki list laati hai.
    Example return: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', ...]
    """
    url = f"{BINANCE_BASE_URL}/api/v3/exchangeInfo"
    data = _get(url)
    if not data:
        return []

    symbols = []
    for s in data.get("symbols", []):
        # hum sirf ACTIVE USDT SPOT pairs lenge (margin/futures nahi)
        if (s.get("status") == "TRADING"
                and s.get("isSpotTradingAllowed", False)
                and s.get("quoteAsset") == "USDT"):
            symbols.append(s["symbol"])
    # Stablecoins / leveraged tokens hatado - ye "movement" wale analysis
    # ke liye meaningful nahi hote (USDC, BUSD, USDT, leveraged tokens).
    BAD = ("USDCUSDT", "BUSDUSDT", "TUSDUSDT", "FDUSDUSDT", "EURUSDT")
    # leveraged tokens ka pattern: UP/DOWN/BULL/BEAR + USDT
    import re
    BAD += tuple(sym for sym in symbols if re.search(r"(UP|DOWN|BULL|BEAR)USDT$", sym))
    symbols = [s for s in symbols if s not in BAD]
    return symbols


def get_24h_tickers(symbols):
    """
    Sabhi symbols ka 24hr market data ek hi batch call me laati hai.
    Returns: pandas DataFrame
    Columns: symbol, lastPrice, priceChangePercent, volume, quoteVolume
    """
    url = f"{BINANCE_BASE_URL}/api/v3/ticker/24hr"
    out = []
    # Binance ki limit ~100 symbols per call, to hum batch me bhejenge
    BATCH = 80
    for i in range(0, len(symbols), BATCH):
        chunk = symbols[i:i + BATCH]
        # Binance ko symbols JSON array format me bhejna hota hai
        params = {"symbols": "[" + ",".join(f'"{s}"' for s in chunk) + "]"}
        data = _get(url, params=params)
        if not data:
            continue
        for item in data:
            out.append({
                "symbol": item["symbol"],
                "lastPrice": float(item["lastPrice"]),
                "priceChangePercent": float(item["priceChangePercent"]),
                "volume": float(item["volume"]),
                "quoteVolume": float(item["quoteVolume"]),  # USDT volume
                "highPrice": float(item["highPrice"]),
                "lowPrice": float(item["lowPrice"]),
                "count": int(item["count"]),  # number of trades
            })
        # Binance API respectful rehna chahiye - thoda rukke
        time.sleep(0.2)
    return pd.DataFrame(out)


def get_klines(symbol, interval="15m", limit=KLINE_LIMIT):
    """
    Ek particular symbol ke liye recent candles (klines) laati hai.
    Returns: pandas DataFrame with columns
        open_time, open, high, low, close, volume, close_time
    """
    url = f"{BINANCE_BASE_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    data = _get(url, params=params)
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_buy_base",
        "taker_buy_quote", "ignore"
    ])
    for col in ["open", "high", "low", "close", "volume", "quote_volume"]:
        df[col] = df[col].astype(float)
    return df
