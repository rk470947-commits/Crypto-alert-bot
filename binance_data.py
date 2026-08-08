# ============================================================
# binance_data.py
# ------------------------------------------------------------
# Binance USD-M Futures market data
#
# Primary endpoint:
#   fapi.binance.com
#
# Failover:
#   fapi1.binance.com
#   fapi2.binance.com
#   fapi3.binance.com
# ============================================================

import time
import requests
import pandas as pd


# ============================================================
# BINANCE FUTURES ENDPOINTS
# ============================================================

BASE_URLS = [
    "https://fapi.binance.com",
    "https://fapi1.binance.com",
    "https://fapi2.binance.com",
    "https://fapi3.binance.com",
]


# Currently working endpoint
ACTIVE_BASE_URL = None


# ============================================================
# SESSION
# ============================================================

SESSION = requests.Session()

SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }
)


# ============================================================
# BINANCE REQUEST
# ============================================================

def binance_request(
    endpoint,
    params=None,
    retries=2
):
    """
    Binance Futures API request.

    Agar ek endpoint 451/403/5xx de,
    to automatically next endpoint try karega.
    """

    global ACTIVE_BASE_URL

    # --------------------------------------------------------
    # Agar pehle koi endpoint successfully kaam kar chuka hai
    # to usko pehle try karo.
    # --------------------------------------------------------

    if ACTIVE_BASE_URL:

        urls = [ACTIVE_BASE_URL]

        for base in BASE_URLS:

            if base != ACTIVE_BASE_URL:
                urls.append(base)

    else:

        urls = BASE_URLS.copy()


    # --------------------------------------------------------
    # Har base URL try karo
    # --------------------------------------------------------

    for base_url in urls:

        url = base_url + endpoint

        for attempt in range(retries):

            try:

                response = SESSION.get(
                    url,
                    params=params,
                    timeout=15
                )

                # ------------------------------------------------
                # Success
                # ------------------------------------------------

                if response.status_code == 200:

                    ACTIVE_BASE_URL = base_url

                    return response.json()


                # ------------------------------------------------
                # Binance region/access restriction
                # ------------------------------------------------

                if response.status_code == 451:

                    print(
                        f"[WARN] 451 blocked: {base_url}"
                    )

                    break


                # ------------------------------------------------
                # Forbidden
                # ------------------------------------------------

                if response.status_code == 403:

                    print(
                        f"[WARN] 403 forbidden: {base_url}"
                    )

                    break


                # ------------------------------------------------
                # Rate limit
                # ------------------------------------------------

                if response.status_code == 429:

                    print(
                        f"[WARN] 429 rate limit: {base_url}"
                    )

                    time.sleep(3)

                    continue


                # ------------------------------------------------
                # Server error
                # ------------------------------------------------

                if response.status_code >= 500:

                    print(
                        f"[WARN] Binance server error "
                        f"{response.status_code}: {base_url}"
                    )

                    time.sleep(2)

                    continue


                # ------------------------------------------------
                # Other HTTP error
                # ------------------------------------------------

                print(
                    f"[WARN] Binance HTTP "
                    f"{response.status_code}: {url}"
                )

                break


            except requests.exceptions.Timeout:

                print(
                    f"[WARN] Timeout: {base_url} "
                    f"(attempt {attempt + 1}/{retries})"
                )

                time.sleep(1)


            except requests.exceptions.RequestException as error:

                print(
                    f"[WARN] Request error: "
                    f"{base_url} - {error}"
                )

                time.sleep(1)


            except Exception as error:

                print(
                    f"[WARN] Unexpected API error: "
                    f"{error}"
                )

                break


    # --------------------------------------------------------
    # Sab endpoints fail
    # --------------------------------------------------------

    print(
        "[ERROR] Binance Futures API ke "
        "kisi bhi endpoint se data nahi mila."
    )

    return None


# ============================================================
# TEST BINANCE FUTURES CONNECTION
# ============================================================

def test_connection():
    """
    Binance Futures connectivity test.
    """

    data = binance_request(
        "/fapi/v1/ping"
    )

    if data is not None:

        print(
            f"[OK] Binance Futures connected: "
            f"{ACTIVE_BASE_URL}"
        )

        return True

    print(
        "[ERROR] Binance Futures connection failed."
    )

    return False


# ============================================================
# GET USDT FUTURES SYMBOLS
# ============================================================

def get_usdt_symbols():

    """
    Active Binance USD-M USDT perpetual futures
    symbols return karta hai.
    """

    data = binance_request(
        "/fapi/v1/exchangeInfo"
    )

    if not data:

        print(
            "[ERROR] exchangeInfo data nahi mila."
        )

        return []


    symbols = []


    for item in data.get(
        "symbols",
        []
    ):

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


    print(
        f"[OK] Found {len(symbols)} "
        f"USDT Futures perpetual pairs"
    )


    return symbols


# ============================================================
# GET 24H TICKERS
# ============================================================

def get_24h_tickers(
    symbols=None
):

    """
    Binance Futures 24H ticker data
    DataFrame ke form mein return karta hai.
    """

    data = binance_request(
        "/fapi/v1/ticker/24hr"
    )

    if not data:

        print(
            "[ERROR] 24H ticker data nahi mila."
        )

        return pd.DataFrame()


    allowed_symbols = None

    if symbols:

        allowed_symbols = set(
            symbols
        )


    rows = []


    for item in data:

        try:

            symbol = item.get(
                "symbol"
            )


            if (
                allowed_symbols is not None
                and symbol not in allowed_symbols
            ):

                continue


            rows.append(
                {
                    "symbol": symbol,

                    "lastPrice": float(
                        item.get(
                            "lastPrice",
                            0
                        )
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
                f"[WARN] Ticker parse failed: "
                f"{error}"
            )

            continue


    if not rows:

        return pd.DataFrame()


    return pd.DataFrame(
        rows
    )


# ============================================================
# GET KLINES
# ============================================================

def get_klines(
    symbol,
    interval="15m",
    limit=100
):

    """
    Binance Futures historical candles.
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

        print(
            f"[WARN] Kline data nahi mila: "
            f"{symbol}"
        )

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


# ============================================================
# END
# ============================================================
