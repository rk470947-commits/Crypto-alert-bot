# ============================================================
# binance_data.py
# ------------------------------------------------------------
# FREE FUTURES MARKET DATA
#
# Binance API GitHub Actions se 451 de raha tha.
# Isliye ab Bybit USDT Perpetual public API use kar rahe hain.
#
# NOTE:
# File name "binance_data.py" abhi same rakha gaya hai
# taaki main.py ke imports change na karne pade.
# ============================================================

import time
import requests
import pandas as pd


# ============================================================
# BYBIT API
# ============================================================

BASE_URL = "https://api.bybit.com"

CATEGORY = "linear"


# ============================================================
# HTTP SESSION
# ============================================================

SESSION = requests.Session()

SESSION.headers.update(
    {
        "User-Agent": "Crypto-Futures-Scanner/1.0",
        "Accept": "application/json",
    }
)


# ============================================================
# API REQUEST
# ============================================================

def bybit_request(
    endpoint,
    params=None,
    retries=3
):
    """
    Bybit public API request.

    Public market-data endpoints ke liye API key
    ki zarurat nahi hai.
    """

    url = BASE_URL + endpoint

    for attempt in range(1, retries + 1):

        try:

            response = SESSION.get(
                url,
                params=params,
                timeout=20
            )

            response.raise_for_status()

            data = response.json()

            ret_code = data.get(
                "retCode",
                -1
            )

            if ret_code != 0:

                print(
                    f"[WARN] Bybit API error: "
                    f"{data.get('retMsg', 'Unknown error')}"
                )

                if attempt < retries:
                    time.sleep(2)

                    continue

                return None

            return data

        except requests.exceptions.RequestException as error:

            print(
                f"[WARN] Bybit connection error "
                f"(attempt {attempt}/{retries}): "
                f"{error}"
            )

            if attempt < retries:
                time.sleep(2)

        except Exception as error:

            print(
                f"[WARN] Unexpected Bybit error: "
                f"{error}"
            )

            return None

    return None


# ============================================================
# GET USDT PERPETUAL SYMBOLS
# ============================================================

def get_usdt_symbols():
    """
    Bybit ke active USDT perpetual symbols return karta hai.

    Bybit category=linear:
    USDT/USDC derivatives ko cover karta hai.
    Hum sirf USDT perpetual contracts lenge.
    """

    symbols = []

    cursor = None

    while True:

        params = {
            "category": CATEGORY,
            "limit": 1000,
        }

        if cursor:
            params["cursor"] = cursor

        data = bybit_request(
            "/v5/market/instruments-info",
            params=params
        )

        if not data:
            break

        result = data.get(
            "result",
            {}
        )

        items = result.get(
            "list",
            []
        )

        for item in items:

            try:

                if (
                    item.get("status") == "Trading"
                    and item.get("contractType")
                    == "LinearPerpetual"
                    and item.get("quoteCoin")
                    == "USDT"
                    and item.get("settleCoin")
                    == "USDT"
                ):

                    symbols.append(
                        item["symbol"]
                    )

            except Exception:

                continue

        cursor = result.get(
            "nextPageCursor"
        )

        if not cursor:
            break

    # Remove duplicates
    symbols = list(
        dict.fromkeys(symbols)
    )

    print(
        f"[OK] Found {len(symbols)} "
        f"Bybit USDT perpetual pairs"
    )

    return symbols


# ============================================================
# GET 24H TICKERS
# ============================================================

def get_24h_tickers(
    symbols=None
):
    """
    Bybit linear futures ke 24H ticker data ko
    same column names mein return karta hai
    jo main.py expect karta hai.
    """

    data = bybit_request(
        "/v5/market/tickers",
        params={
            "category": CATEGORY
        }
    )

    if not data:

        print(
            "[ERROR] Bybit 24H ticker data nahi mila."
        )

        return pd.DataFrame()


    result = data.get(
        "result",
        {}
    )

    ticker_list = result.get(
        "list",
        []
    )


    if not ticker_list:

        print(
            "[ERROR] Bybit ticker list empty hai."
        )

        return pd.DataFrame()


    allowed_symbols = None

    if symbols:

        allowed_symbols = set(
            symbols
        )


    rows = []


    for item in ticker_list:

        try:

            symbol = item.get(
                "symbol"
            )


            if (
                allowed_symbols is not None
                and symbol not in allowed_symbols
            ):

                continue


            # Bybit ticker fields:
            #
            # lastPrice
            # price24hPcnt
            # turnover24h
            # volume24h


            last_price = float(
                item.get(
                    "lastPrice",
                    0
                )
            )


            price_change_pct = (
                float(
                    item.get(
                        "price24hPcnt",
                        0
                    )
                )
                * 100
            )


            quote_volume = float(
                item.get(
                    "turnover24h",
                    0
                )
            )


            base_volume = float(
                item.get(
                    "volume24h",
                    0
                )
            )


            rows.append(
                {
                    "symbol": symbol,

                    "lastPrice": last_price,

                    "priceChangePercent":
                        price_change_pct,

                    "quoteVolume":
                        quote_volume,

                    # Bybit ticker response mein
                    # Binance jaisa trade count nahi hai.
                    # Isliye safe default use kar rahe hain.
                    "count": 0,

                    "highPrice": float(
                        item.get(
                            "highPrice24h",
                            0
                        )
                    ),

                    "lowPrice": float(
                        item.get(
                            "lowPrice24h",
                            0
                        )
                    ),

                    "volume": base_volume,
                }
            )


        except Exception as error:

            print(
                f"[WARN] Ticker parse failed: "
                f"{error}"
            )

            continue


    if not rows:

        return pd.DataFrame()


    df = pd.DataFrame(
        rows
    )


    print(
        f"[OK] Received 24H data for "
        f"{len(df)} symbols"
    )


    return df


# ============================================================
# GET 15-MINUTE KLINES
# ============================================================

def get_klines(
    symbol,
    interval="15m",
    limit=100
):
    """
    Bybit Futures historical candles.

    Main.py/scoring.py ke liye Binance-compatible
    DataFrame columns return karta hai.
    """

    # --------------------------------------------------------
    # Binance-style interval ko Bybit interval mein convert
    # --------------------------------------------------------

    interval_map = {
        "1m": "1",
        "3m": "3",
        "5m": "5",
        "15m": "15",
        "30m": "30",
        "1h": "60",
        "2h": "120",
        "4h": "240",
        "6h": "360",
        "12h": "720",
        "1d": "D",
        "1w": "W",
        "1M": "M",
    }


    bybit_interval = interval_map.get(
        interval,
        interval
    )


    data = bybit_request(
        "/v5/market/kline",
        params={
            "category": CATEGORY,
            "symbol": symbol,
            "interval": bybit_interval,
            "limit": min(
                int(limit),
                1000
            ),
        }
    )


    if not data:

        print(
            f"[WARN] Kline data nahi mila: "
            f"{symbol}"
        )

        return pd.DataFrame()


    result = data.get(
        "result",
        {}
    )


    candle_list = result.get(
        "list",
        []
    )


    if not candle_list:

        return pd.DataFrame()


    # Bybit response:
    #
    # [startTime,
    #  open,
    #  high,
    #  low,
    #  close,
    #  volume,
    #  turnover]
    #
    # Response reverse chronological order mein hota hai.
    # Hum oldest -> newest karenge.


    candle_list = list(
        reversed(candle_list)
    )


    rows = []


    for candle in candle_list:

        try:

            if len(candle) < 7:
                continue


            open_time = int(
                candle[0]
            )

            open_price = float(
                candle[1]
            )

            high_price = float(
                candle[2]
            )

            low_price = float(
                candle[3]
            )

            close_price = float(
                candle[4]
            )

            volume = float(
                candle[5]
            )

            quote_volume = float(
                candle[6]
            )


            rows.append(
                {
                    "open_time":
                        open_time,

                    "open":
                        open_price,

                    "high":
                        high_price,

                    "low":
                        low_price,

                    "close":
                        close_price,

                    "volume":
                        volume,

                    "close_time":
                        open_time,

                    "quote_volume":
                        quote_volume,

                    "trades":
                        0,

                    "taker_buy_base":
                        0,

                    "taker_buy_quote":
                        0,

                    "ignore":
                        0,
                }
            )


        except Exception as error:

            print(
                f"[WARN] Candle parse failed "
                f"for {symbol}: {error}"
            )

            continue


    if not rows:

        return pd.DataFrame()


    df = pd.DataFrame(
        rows
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


# ============================================================
# CONNECTION TEST
# ============================================================

def test_connection():

    """
    Simple Bybit public API connection test.
    """

    data = bybit_request(
        "/v5/market/time"
    )


    if data:

        print(
            "[OK] Bybit Futures API connected."
        )

        return True


    print(
        "[ERROR] Bybit Futures API connection failed."
    )

    return False


# ============================================================
# END
# ============================================================
