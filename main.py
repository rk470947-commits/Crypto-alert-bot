     1	# ============================================================
     2	# main.py - BOT KA MAIN ENGINE
     3	# ------------------------------------------------------------
     4	# Ye file pure bot ko chalati hai. Har SCAN_INTERVAL_SECONDS
     5	# pe ye:
     6	#   1. Binance se saare USDT pairs ka 24h data laati hai
     7	#   2. Volume filter lagati hai
     8	#   3. Har coin ko score karti hai
     9	#   4. Top N coins ko Telegram pe bhejti hai
    10	# ============================================================
    11	
    12	import time
    13	import traceback
    14	from datetime import datetime
    15	from config import (
    16	    SCAN_INTERVAL_SECONDS, TOP_N_COINS,
    17	    MIN_24H_VOLUME_USDT, DRY_RUN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    18	)
    19	from binance_data import get_usdt_symbols, get_24h_tickers
    20	from scoring import score_symbol
    21	from telegram_bot import send_telegram, format_alert
    22	
    23	
    24	def run_once():
    25	    """Ek poori scan chalati hai aur top coins ko Telegram pe bhejti hai."""
    26	    print(f"\n[{datetime.utcnow().strftime('%H:%M:%S')}] Scan shuru...")
    27	
    28	    # 1) Symbols ki list
    29	    symbols = get_usdt_symbols()
    30	    print(f"  - Found {len(symbols)} USDT pairs on Binance")
    31	    if not symbols:
    32	        print("  - Symbols nahi mile. Internet/API check karo.")
    33	        return
    34	
    35	    # 2) 24hr tickers batch me
    36	    df = get_24h_tickers(symbols)
    37	    print(f"  - 24h tickers mila: {len(df)} symbols ke liye")
    38	    if df.empty:
    39	        return
    40	
    41	    # 3) Volume filter
    42	    df = df[df["quoteVolume"] >= MIN_24H_VOLUME_USDT]
    43	    print(f"  - Volume filter ke baad: {len(df)} coins")
    44	
    45	    # 4) Scoring  -  sirf candidates pe klines call karenge
    46	    # Pehle quick-score (volume + change) se  candidate chunte hain
    47	    df["quick_score"] = (
    48	        (df["quoteVolume"].rank(pct=True)) * 0.5 +
    49	        (df["priceChangePercent"].abs().rank(pct=True)) * 0.3 +
    50	        (df["count"].rank(pct=True)) * 0.2
    51	    )
    52	    candidates = df.sort_values("quick_score", ascending=False).head(50)
    53	
    54	    results = []
    55	    for _, row in candidates.iterrows():
    56	        try:
    57	            r = score_symbol(
    58	                symbol=row["symbol"],
    59	                last_price=row["lastPrice"],
    60	                change_pct=row["priceChangePercent"],
    61	                quote_volume=row["quoteVolume"],
    62	                trade_count=row["count"],
    63	            )
    64	            # Price info bhi attach kar do display ke liye
    65	            r["price"] = row["lastPrice"]
    66	            r["change_pct"] = row["priceChangePercent"]
    67	            r["quote_volume"] = row["quoteVolume"]
    68	            results.append(r)
    69	        except Exception as e:
    70	            print(f"  [warn] {row['symbol']} score fail: {e}")
    71	            continue
    72	
    73	    results.sort(key=lambda x: x["score"], reverse=True)
    74	    top = results[:TOP_N_COINS]
    75	    print(f"  - Top {TOP_N_COINS} coins shortlist ho gayi.")
    76	
    77	    # 5) Telegram pe bhejo
    78	    if not top:
    79	        print("  - Koi valid result nahi mila.")
    80	        return
    81	    msg = format_alert(top)
    82	    send_telegram(msg)
    83	
    84	
    85	def main():
    86	    print("===========================================")
    87	    print(" Binance Crypto Screener Telegram Bot")
    88	    print(" Har", SCAN_INTERVAL_SECONDS, "second pe scan chalega.")
    89	    print(f" DRY_RUN = {DRY_RUN}")
    90	    if not DRY_RUN:
    91	        if TELEGRAM_BOT_TOKEN.startswith("PASTE") or TELEGRAM_CHAT_ID.startswith("PASTE"):
    92	            print(" ERROR: config.py me Token / Chat ID paste karo!")
    93	            return
    94	    print("===========================================")
    95	
    96	    while True:
    97	        try:
    98	            run_once()
    99	        except KeyboardInterrupt:
   100	            print("\nBot band ho raha hai (Ctrl+C). Bye!")
   101	            break
   102	        except Exception as e:
   103	            print(f"[fatal] Loop error: {e}")
   104	            traceback.print_exc()
   105	        print(f"Next scan in {SCAN_INTERVAL_SECONDS} seconds... (Ctrl+C to stop)")
   106	        time.sleep(SCAN_INTERVAL_SECONDS)
   107	
   108	
   109	if __name__ == "__main__":
   110	    main()
