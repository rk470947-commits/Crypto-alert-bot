# ============================================================
# binance_data.py
# ------------------------------------------------------------
# Binance USDT Futures se market data lene ke functions
# ============================================================

import time
import requests
import pandas as pd


BASE_URL = "https://fapi.binance.com"


# ============================================================
# BINANCE API REQUEST
# ============================================================

def binance_request(endpoint, params=None, retries=3):
    """Binance Futures API se data fetch karta hai."""

    url = BASE_URL + endpoint

    for attempt in range(retries):

        try:

            response = requests.get(
                url,
                params=params,
                timeout=20
            )

            response.raise_for_status()

            return response.json()

        except Exception as error:

            print(
                f"[WARN] Binance API error "
                f"(attempt {attempt + 1}/{retries}): {error}"
            )

            if attempt < retries - 1:
                time.sleep(2)

    return None


# ============================================================
# GET USDT FUTURES SYMBOLS
# ============================================================

def get_usdt_symbols():
    """
    Binance USDT-M Futures ke active USDT symbols return karta hai.
    """

    data = binance_request("/fapi/v1/exchangeInfo")

    if not data:
        return []

    symbols = []

    for item in data.get("symbols", []):

        try:

            if (
                item.get("quoteAsset") == "USDT"
                and item.get("status") == "TRADING"
                and item.get("contractType") == "PERPETUAL"
            ):

                symbols.append(
                    item["symbol"]
                )

        except Exception:
            continue

    return symbols


# ============================================================
# GET 24H TICKERS
# ============================================================

def get_24h_tickers(symbols=None):
    """
    Binance Futures ke 24H ticker data ko DataFrame me return karta hai.
    """

    data = binance_request("/fapi/v1/ticker/24hr")

    if not data:
        return pd.DataFrame()

    rows = []

    allowed_symbols = set(symbols) if symbols else None

    for item in data:

        try:

            symbol = item.get("symbol")

            if allowed_symbols is not None:
                if symbol not in allowed_symbols:
                    continue

            rows.append(
                {
                    "symbol": symbol,

                    "lastPrice": float(
                        item.get("lastPrice", 0)
                    ),

                    "priceChangePercent": float(
                        item.get(
                            "priceChangePercent",
                            0
                        )
                    ),

                    "quoteVolume": float(
                        item.get(
                            "quoteVolume",
                            0
                        )
                    ),

                    "count": int(
                        item.get(
                            "count",
                            0
                        )
                    ),

                    "highPrice": float(
                        item.get(
                            "highPrice",
                            0
                        )
                    ),

                    "lowPrice": float(
                        item.get(
                            "lowPrice",
                            0
                        )
                    ),

                    "volume": float(
                        item.get(
                            "volume",
                            0
                        )
                    ),
                }
            )

        except Exception as error:

            print(
                f"[WARN] Ticker parse failed: {error}"
            )

            continue

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    return df


# ============================================================
# GET KLINES
# ============================================================

def get_klines(
    symbol,
    interval="15m",
    limit=100
):
    """
    Kisi symbol ke historical candles return karta hai.
    """

    data = binance_request(
        "/fapi/v1/klines",
        params={
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }
    )

    if not data:
        return pd.DataFrame()

    columns = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_volume",
        "trades",
        "taker_buy_base",
        "taker_buy_quote",
        "ignore",
    ]

    try:

        df = pd.DataFrame(
            data,
            columns=columns
        )

        numeric_columns = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "quote_volume",
        ]

        for column in numeric_columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        return df

    except Exception as error:

        print(
            f"[WARN] Kline parsing failed "
            f"for {symbol}: {error}"
        )

        return pd.DataFrame()
