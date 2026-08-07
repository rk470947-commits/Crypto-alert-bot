     1	# ============================================================
     2	# binance_data.py - BINANCE SE DATA LANA
     3	# ------------------------------------------------------------
     4	# Ye file Binance ki public API se:
     5	#   1. Saari USDT trading pairs ki list laati hai
     6	#   2. Sabka 24hr ticker data laati hai (volume, price change)
     7	#   3. Top candidates ke liye 15-min candles laati hai
     8	# ============================================================
     9	
    10	import requests
    11	import time
    12	import pandas as pd
    13	from config import BINANCE_BASE_URL, KLINE_LIMIT
    14	
    15	
    16	def _get(url, params=None, retries=3):
    17	    """Request bhejta hai aur agar fail ho to dobara try karta hai."""
    18	    for attempt in range(retries):
    19	        try:
    20	            r = requests.get(url, params=params, timeout=15)
    21	            r.raise_for_status()
    22	            return r.json()
    23	        except Exception as e:
    24	            print(f"[warn] API call fail (try {attempt+1}/{retries}): {e}")
    25	            time.sleep(2)
    26	    return None
    27	
    28	
    29	def get_usdt_symbols():
    30	    """
    31	    Saari USDT trading pairs ki list laati hai.
    32	    Example return: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', ...]
    33	    """
    34	    url = f"{BINANCE_BASE_URL}/api/v3/exchangeInfo"
    35	    data = _get(url)
    36	    if not data:
    37	        return []
    38	
    39	    symbols = []
    40	    for s in data.get("symbols", []):
    41	        # hum sirf ACTIVE USDT SPOT pairs lenge (margin/futures nahi)
    42	        if (s.get("status") == "TRADING"
    43	                and s.get("isSpotTradingAllowed", False)
    44	                and s.get("quoteAsset") == "USDT"):
    45	            symbols.append(s["symbol"])
    46	    # Stablecoins / leveraged tokens hatado - ye "movement" wale analysis
    47	    # ke liye meaningful nahi hote (USDC, BUSD, USDT, leveraged tokens).
    48	    BAD = ("USDCUSDT", "BUSDUSDT", "TUSDUSDT", "FDUSDUSDT", "EURUSDT")
    49	    # leveraged tokens ka pattern: UP/DOWN/BULL/BEAR + USDT
    50	    import re
    51	    BAD += tuple(sym for sym in symbols if re.search(r"(UP|DOWN|BULL|BEAR)USDT$", sym))
    52	    symbols = [s for s in symbols if s not in BAD]
    53	    return symbols
    54	
    55	
    56	def get_24h_tickers(symbols):
    57	    """
    58	    Sabhi symbols ka 24hr market data ek hi batch call me laati hai.
    59	    Returns: pandas DataFrame
    60	    Columns: symbol, lastPrice, priceChangePercent, volume, quoteVolume
    61	    """
    62	    url = f"{BINANCE_BASE_URL}/api/v3/ticker/24hr"
    63	    out = []
    64	    # Binance ki limit ~100 symbols per call, to hum batch me bhejenge
    65	    BATCH = 80
    66	    for i in range(0, len(symbols), BATCH):
    67	        chunk = symbols[i:i + BATCH]
    68	        # Binance ko symbols JSON array format me bhejna hota hai
    69	        params = {"symbols": "[" + ",".join(f'"{s}"' for s in chunk) + "]"}
    70	        data = _get(url, params=params)
    71	        if not data:
    72	            continue
    73	        for item in data:
    74	            out.append({
    75	                "symbol": item["symbol"],
    76	                "lastPrice": float(item["lastPrice"]),
    77	                "priceChangePercent": float(item["priceChangePercent"]),
    78	                "volume": float(item["volume"]),
    79	                "quoteVolume": float(item["quoteVolume"]),  # USDT volume
    80	                "highPrice": float(item["highPrice"]),
    81	                "lowPrice": float(item["lowPrice"]),
    82	                "count": int(item["count"]),  # number of trades
    83	            })
    84	        # Binance API respectful rehna chahiye - thoda rukke
    85	        time.sleep(0.2)
    86	    return pd.DataFrame(out)
    87	
    88	
    89	def get_klines(symbol, interval="15m", limit=KLINE_LIMIT):
    90	    """
    91	    Ek particular symbol ke liye recent candles (klines) laati hai.
    92	    Returns: pandas DataFrame with columns
    93	        open_time, open, high, low, close, volume, close_time
    94	    """
    95	    url = f"{BINANCE_BASE_URL}/api/v3/klines"
    96	    params = {"symbol": symbol, "interval": interval, "limit": limit}
    97	    data = _get(url, params=params)
    98	    if not data:
    99	        return pd.DataFrame()
   100	    df = pd.DataFrame(data, columns=[
   101	        "open_time", "open", "high", "low", "close", "volume",
   102	        "close_time", "quote_volume", "trades", "taker_buy_base",
   103	        "taker_buy_quote", "ignore"
   104	    ])
   105	    for col in ["open", "high", "low", "close", "volume", "quote_volume"]:
   106	        df[col] = df[col].astype(float)
   107	    return df
