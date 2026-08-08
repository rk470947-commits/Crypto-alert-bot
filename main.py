# ============================================================
# main.py - BINANCE FUTURES SCANNER
# ------------------------------------------------------------
# Ek scan:
#   1. Binance se USDT Futures pairs leta hai
#   2. 24h market data leta hai
#   3. Volume filter lagata hai
#   4. Top candidates ko scoring.py se score karta hai
#   5. Top coins ko Telegram par bhejta hai
#
# GitHub Actions ke liye designed:
#   - Ek run = ek scan
#   - Continuous while-loop nahi hai
#   - Telegram credentials environment variables se aayenge
# ============================================================

import os
import traceback
from datetime import datetime, timezone

from binance_data import get_usdt_symbols, get_24h_tickers
from scoring import score_symbol
from telegram_bot import send_telegram, format_alert


# ============================================================
# SETTINGS
# ============================================================

TOP_N_COINS = int(os.getenv("TOP_N_COINS", "10"))

MIN_24H_VOLUME_USDT = float(
    os.getenv("MIN_24H_VOLUME_USDT", "1000000")
)

CANDIDATE_COUNT = int(
    os.getenv("CANDIDATE_COUNT", "50")
)

DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"


# ============================================================
# RUN ONE SCAN
# ============================================================

def run_once():
    """Binance Futures ka ek complete scan chalata hai."""

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    print("\n===========================================")
    print(" Binance Futures Scanner")
    print(" Scan time:", now)
    print("===========================================")

    # --------------------------------------------------------
    # 1) Binance USDT Futures symbols
    # --------------------------------------------------------

    print("\n[1/5] Binance USDT pairs fetch ho rahe hain...")

    symbols = get_usdt_symbols()

    print(f"  Found {len(symbols)} USDT Futures pairs")

    if not symbols:
        print("  ERROR: Koi USDT pair nahi mila.")
        return False

    # --------------------------------------------------------
    # 2) 24H ticker data
    # --------------------------------------------------------

    print("\n[2/5] 24H market data fetch ho raha hai...")

    df = get_24h_tickers(symbols)

    print(f"  Received data for {len(df)} symbols")

    if df.empty:
        print("  ERROR: 24H ticker data empty hai.")
        return False

    # --------------------------------------------------------
    # 3) Volume filter
    # --------------------------------------------------------

    print("\n[3/5] Volume filter apply ho raha hai...")

    before_count = len(df)

    df = df[
        df["quoteVolume"] >= MIN_24H_VOLUME_USDT
    ].copy()

    print(
        f"  Volume filter: "
        f"{before_count} -> {len(df)} coins"
    )

    if df.empty:
        print("  Koi coin minimum volume filter pass nahi hua.")
        return False

    # --------------------------------------------------------
    # 4) Quick candidate selection
    # --------------------------------------------------------

    print("\n[4/5] Best candidates select ho rahe hain...")

    # Rank based quick score:
    # Volume        = 50%
    # Price movement = 30%
    # Trade count    = 20%

    df["quick_score"] = (
        df["quoteVolume"].rank(pct=True) * 0.50
        +
        df["priceChangePercent"].abs().rank(pct=True) * 0.30
        +
        df["count"].rank(pct=True) * 0.20
    )

    candidates = (
        df.sort_values(
            "quick_score",
            ascending=False
        )
        .head(CANDIDATE_COUNT)
    )

    print(
        f"  {len(candidates)} candidates detailed scoring ke liye select hue."
    )

    # --------------------------------------------------------
    # Detailed scoring
    # --------------------------------------------------------

    results = []

    for _, row in candidates.iterrows():

        symbol = row["symbol"]

        try:

            result = score_symbol(
                symbol=symbol,
                last_price=row["lastPrice"],
                change_pct=row["priceChangePercent"],
                quote_volume=row["quoteVolume"],
                trade_count=row["count"],
            )

            # Display information attach karna
            result["symbol"] = symbol
            result["price"] = row["lastPrice"]
            result["change_pct"] = row["priceChangePercent"]
            result["quote_volume"] = row["quoteVolume"]
            result["trade_count"] = row["count"]

            results.append(result)

        except Exception as error:

            print(
                f"  [WARN] {symbol} scoring failed: {error}"
            )

            continue

    # --------------------------------------------------------
    # Sort by final score
    # --------------------------------------------------------

    if not results:

        print("  Koi valid scoring result nahi mila.")
        return False

    results.sort(
        key=lambda x: x.get("score", 0),
        reverse=True
    )

    top = results[:TOP_N_COINS]

    print(
        f"\n  TOP {len(top)} coins:"
    )

    for index, item in enumerate(top, start=1):

        print(
            f"  {index}. "
            f"{item.get('symbol', 'UNKNOWN')} "
            f"| Score: {item.get('score', 0)} "
            f"| Change: {item.get('change_pct', 0):.2f}%"
        )

    # --------------------------------------------------------
    # 5) Telegram
    # --------------------------------------------------------

    print("\n[5/5] Telegram alert prepare ho raha hai...")

    message = format_alert(top)

    if not message:
        print("  Telegram message empty hai.")
        return False

    # --------------------------------------------------------
    # DRY RUN
    # --------------------------------------------------------

    if DRY_RUN:

        print("\n========== DRY RUN ==========")
        print(message)
        print("=============================\n")

        return True

    # --------------------------------------------------------
    # Telegram send
    # --------------------------------------------------------

    try:

        send_telegram(message)

        print("  Telegram alert successfully sent.")

    except Exception as error:

        print(
            f"  Telegram send failed: {error}"
        )

        traceback.print_exc()

        return False

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print("===========================================")
    print(" Binance Futures Crypto Scanner")
    print("===========================================")

    print(
        f"TOP_N_COINS          = {TOP_N_COINS}"
    )

    print(
        f"MIN_24H_VOLUME_USDT  = {MIN_24H_VOLUME_USDT:,.0f}"
    )

    print(
        f"CANDIDATE_COUNT      = {CANDIDATE_COUNT}"
    )

    print(
        f"DRY_RUN              = {DRY_RUN}"
    )

    print("===========================================")

    try:

        success = run_once()

        if success:
            print("\nScan completed successfully.")
        else:
            print("\nScan completed with warnings/errors.")

    except Exception as error:

        print("\n[FATAL ERROR]")
        print(error)

        traceback.print_exc()

        # GitHub Actions ko failure status dene ke liye
        raise


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
