1	# ============================================================
     2	# scoring.py - SCORE AUR RATING CALCULATION
     3	# ------------------------------------------------------------
     4	# Ye file decide karti hai kaun-sa coin "movement" ke liye ready hai.
     5	# Hum 4 cheezein mila ke ek 0-100 score banate hain:
     6	#   1. 24h volume kitna hai aur kitna trade ho raha hai
     7	#   2. Pichle 15-minute candles me price kitna hil rahi hai
     8	#   3. RSI (Relative Strength Index) - overbought / oversold
     9	#   4. Volatility (candles ka high-low range)
    10	# Score ke basis pe A / B / C rating di jaati hai.
    11	# ============================================================
    12	
    13	import pandas as pd
    14	import numpy as np
    15	from binance_data import get_klines
    16	
    17	
    18	# ---------- Helper functions (indicators) ----------
    19	
    20	def compute_rsi(closes, period=14):
    21	    """
    22	    RSI - Relative Strength Index nikalta hai.
    23	    > 70 = overbought (zyada kharida gaya, girne ka risk)
    24	    < 30 = oversold (zyada becha gaya, uthne ka chance)
    25	    30-70 ke beech = neutral / calm
    26	    """
    27	    closes = pd.Series(closes).astype(float)
    28	    delta = closes.diff()
    29	    gain = delta.clip(lower=0)
    30	    loss = -delta.clip(upper=0)
    31	    avg_gain = gain.rolling(period).mean()
    32	    avg_loss = loss.rolling(period).mean()
    33	    rs = avg_gain / avg_loss.replace(0, np.nan)
    34	    rsi = 100 - (100 / (1 + rs))
    35	    return rsi.fillna(50).iloc[-1]
    36	
    37	
    38	def compute_volatility_pct(df):
    39	    """
    40	    Pichle candles ka average (high-low)/close ratio (%).
    41	    Zyada value = zyada price movement / volatility.
    42	    """
    43	    if df.empty:
    44	        return 0.0
    45	    rng = (df["high"] - df["low"]) / df["close"]
    46	    return float(rng.mean() * 100)
    47	
    48	
    49	def compute_relative_volume(df, window=20):
    50	    """
    51	    Last candle ka volume vs pichle 'window' candles ka avg volume.
    52	    > 1.5 matlab aaj/aise volume spike hai - market me entry ho rahi hai.
    53	    """
    54	    if df.empty or len(df) < 5:
    55	        return 0.0
    56	    vols = df["volume"].astype(float).values
    57	    if len(vols) < window:
    58	        base = vols[:-1].mean()
    59	    else:
    60	        base = vols[-(window+1):-1].mean()
    61	    if base == 0:
    62	        return 0.0
    63	    return float(vols[-1] / base)
    64	
    65	
    66	# ---------- Main scoring function ----------
67	
    68	def score_symbol(symbol, last_price, change_pct, quote_volume, trade_count):
    69	    """
    70	    Ek symbol ke liye 0-100 score aur A/B/C rating nikalta hai.
    71	    Returns: dict with score, rating, reason, sub_scores
    72	    """
    73	    # 1) Volume sub-score (max 30)
    74	    # 50M USDT volume good, 500M+ excellent
    75	    vol_score = min(30.0, np.log10(max(quote_volume, 1)) * 6)
    76	
    77	    # 2) Trade count sub-score (max 15)
    78	    # Zyada trades = zyada active
    79	    trade_score = min(15.0, np.log10(max(trade_count, 1)) * 3)
    80	
    81	    # 3) Recent 15m change sub-score (max 15)
    82	    # Strong positive move (mild) = bullish, very big move = risky
    83	    abs_change = abs(change_pct)
    84	    if change_pct > 0:
    85	        chg_score = min(15.0, abs_change * 1.5)
    86	    else:
    87	        chg_score = min(15.0, abs_change * 0.7)  # bade drop ko thoda kam score
    88	
    89	    # 4) Candle-based indicators (klines se)
    90	    df = get_klines(symbol, interval="15m")
    91	    if df.empty or len(df) < 10:
    92	        return {
    93	            "symbol": symbol,
    94	            "score": 0.0,
    95	            "rating": "C",
    96	            "reason": "data-not-enough",
    97	            "sub_scores": {"volume": vol_score, "trade": trade_score, "change": chg_score},
    98	        }
    99	
   100	    rsi = compute_rsi(df["close"])
   101	    vol15 = compute_volatility_pct(df)
   102	    rel_vol = compute_relative_volume(df)
   103	
   104	    # 5) RSI sub-score (max 20)
   105	    # RSI 50-65 = best (trend building), 30-50 = oversold bounce, 70+ = risky
   106	    if 50 <= rsi <= 65:
   107	        rsi_score = 20.0
   108	    elif 30 <= rsi < 50:
   109	        rsi_score = 16.0
   110	    elif 65 < rsi <= 75:
   111	        rsi_score = 12.0
   112	    elif 75 < rsi:
   113	        rsi_score = 5.0
   114	    else:  # < 30
   115	        rsi_score = 14.0
   116	
   117	    # 6) Volatility sub-score (max 10)
   118	    # Thodi-volatility healthy; 0% flat boring; bahut zyada = risky
   119	    if 0.5 <= vol15 <= 3.0:
   120	        vol_sub = 10.0
121	    elif vol15 < 0.5:
   122	        vol_sub = 3.0
   123	    elif 3.0 < vol15 <= 6.0:
   124	        vol_sub = 7.0
   125	    else:
   126	        vol_sub = 4.0
   127	
   128	    # 7) Relative volume spike sub-score (max 10)
   129	    if rel_vol >= 2.5:
   130	        spike_score = 10.0
   131	    elif rel_vol >= 1.5:
   132	        spike_score = 7.0
   133	    elif rel_vol >= 1.1:
   134	        spike_score = 4.0
   135	    else:
   136	        spike_score = 1.0
   137	
   138	    total = vol_score + trade_score + chg_score + rsi_score + vol_sub + spike_score
   139	    total = min(100.0, total)
   140	
   141	    # ---- Rating bucket ----
   142	    if total >= 75:
   143	        rating = "A"
   144	    elif total >= 55:
   145	        rating = "B"
   146	    else:
   147	        rating = "C"
   148	
   149	    # ek chhoti si readable reason
   150	    if rel_vol >= 2.0:
   151	        rsn = "volume-spike"
   152	    elif rsi < 30:
   153	        rsn = "oversold-rebound"
   154	    elif rsi > 70:
   155	        rsn = "overbought-risky"
   156	    elif 50 <= rsi <= 65 and vol15 >= 1.0:
   157	        rsn = "building-trend"
   158	    else:
   159	        rsn = "active-mover"
   160	
   161	    return {
   162	        "symbol": symbol,
   163	        "score": round(total, 2),
   164	        "rating": rating,
   165	        "reason": rsn,
   166	        "rsi": round(rsi, 1),
   167	        "vol15_pct": round(vol15, 2),
   168	        "rel_volume": round(rel_vol, 2),
   169	        "sub_scores": {
   170	            "volume": round(vol_score, 1),
   171	            "trade": round(trade_score, 1),
   172	            "change": round(chg_score, 1),
   173	            "rsi": round(rsi_score, 1),
   174	            "volatility": round(vol_sub, 1),
   175	            "spike": round(spike_score, 1),
   176	        },
   177	    }
   178	
   179	
   180	def rate_to_emoji(rating):
   181	    return {"A": "🟢", "B": "🟡", "C": "🔴"}.get(rating, "⚪")
