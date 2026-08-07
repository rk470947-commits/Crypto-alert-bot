# ============================================================
# main.py - BOT KA MAIN ENGINE
# ------------------------------------------------------------
# Ye file pure bot ko chalati hai. Har SCAN_INTERVAL_SECONDS
# pe ye:
#   1. Binance se saare USDT pairs ka 24h data laati hai
#   2. Volume filter lagati hai
#   3. Har coin ko score karti hai
#   4. Top N coins ko Telegram pe bhejti hai
# ============================================================

import time
import traceback
from datetime import datetime
from config import (
    SCAN_INTERVAL_SECONDS, TOP_N_COINS,
    MIN_24H_VOLUME_USDT, DRY_RUN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
)
from binance_data import get_usdt_symbols, get_24h_tickers
from scoring import score_symbol
from telegram_bot import send_telegram, format_alert


def run_once():
    """Ek poori scan chalati hai aur top coins ko Telegram pe bhejti hai."""
    print(f"\n[{datetime.utcnow().strftime('%H:%M:%S')}] Scan shuru...")

    # 1) Symbols ki list
    symbols = get_usdt_symbols()
    print(f"  - Found {len(symbols)} USDT pairs on Binance")
    if not symbols:
        print("  - Symbols nahi mile. Internet/API check karo.")
        return

    # 2) 24hr tickers batch me
    df = get_24h_tickers(symbols)
    print(f"  - 24h tickers mila: {len(df)} symbols ke liye")
    if df.empty:
        return

    # 3) Volume filter
    df = df[df["quoteVolume"] >= MIN_24H_VOLUME_USDT]
    print(f"  - Volume filter ke baad: {len(df)} coins")

    # 4) Scoring  -  sirf candidates pe klines call karenge
    # Pehle quick-score (volume + change) se  candidate chunte hain
    df["quick_score"] = (
        (df["quoteVolume"].rank(pct=True)) * 0.5 +
        (df["priceChangePercent"].abs().rank(pct=True)) * 0.3 +
        (df["count"].rank(pct=True)) * 0.2
    )
    candidates = df.sort_values("quick_score", ascending=False).head(50)

    results = []
    for _, row in candidates.iterrows():
        try:
            r = score_symbol(
                symbol=row["symbol"],
                last_price=row["lastPrice"],
                change_pct=row["priceChangePercent"],
                quote_volume=row["quoteVolume"],
                trade_count=row["count"],
            )
            # Price info bhi attach kar do display ke liye
            r["price"] = row["lastPrice"]
            r["change_pct"] = row["priceChangePercent"]
            r["quote_volume"] = row["quoteVolume"]
            results.append(r)
        except Exception as e:
            print(f"  [warn] {row['symbol']} score fail: {e}")
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    top = results[:TOP_N_COINS]
    print(f"  - Top {TOP_N_COINS} coins shortlist ho gayi.")

    # 5) Telegram pe bhejo
    if not top:
        print("  - Koi valid result nahi mila.")
        return
    msg = format_alert(top)
    send_telegram(msg)


def main():
    print("===========================================")
    print(" Binance Crypto Screener Telegram Bot")
    print(" Har", SCAN_INTERVAL_SECONDS, "second pe scan chalega.")
    print(f" DRY_RUN = {DRY_RUN}")
    if not DRY_RUN:
        if TELEGRAM_BOT_TOKEN.startswith("PASTE") or TELEGRAM_CHAT_ID.startswith("PASTE"):
            print(" ERROR: config.py me Token / Chat ID paste karo!")
            return
    print("===========================================")

    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            print("\nBot band ho raha hai (Ctrl+C). Bye!")
            break
        except Exception as e:
            print(f"[fatal] Loop error: {e}")
            traceback.print_exc()
        print(f"Next scan in {SCAN_INTERVAL_SECONDS} seconds... (Ctrl+C to stop)")
        time.sleep(SCAN_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
