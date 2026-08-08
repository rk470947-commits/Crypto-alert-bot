# ============================================================
# telegram_bot.py
# ------------------------------------------------------------
# Telegram Bot ko message bhejne ke functions
# ============================================================

import os
import requests


# ============================================================
# TELEGRAM SETTINGS
# ============================================================

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN",
    ""
)

TELEGRAM_CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID",
    ""
)


# ============================================================
# SEND TELEGRAM MESSAGE
# ============================================================

def send_telegram(message):
    """
    Telegram Bot API ke through message bhejta hai.
    """

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN environment variable nahi mila."
        )

    if not TELEGRAM_CHAT_ID:
        raise ValueError(
            "TELEGRAM_CHAT_ID environment variable nahi mila."
        )

    url = (
        "https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    response = requests.post(
        url,
        json=payload,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("ok"):
        raise RuntimeError(
            f"Telegram API error: {data}"
        )

    return data


# ============================================================
# FORMAT ALERT
# ============================================================

def format_alert(results):
    """
    Scanner ke results ko readable Telegram message mein
    convert karta hai.
    """

    if not results:
        return "⚠️ Koi strong result nahi mila."


    lines = []

    lines.append(
        "🚨 <b>BINANCE FUTURES SCANNER</b>"
    )

    lines.append(
        "━━━━━━━━━━━━━━━━━━━━"
    )

    lines.append(
        f"📊 <b>Top {len(results)} Signals</b>"
    )

    lines.append("")


    for index, item in enumerate(
        results,
        start=1
    ):

        symbol = item.get(
            "symbol",
            "UNKNOWN"
        )

        score = item.get(
            "score",
            0
        )

        direction = item.get(
            "direction",
            "NEUTRAL"
        )

        quality = item.get(
            "quality",
            "UNKNOWN"
        )

        price = item.get(
            "price",
            0
        )

        change_pct = item.get(
            "change_pct",
            0
        )

        rsi = item.get(
            "rsi"
        )

        volume_ratio = item.get(
            "volume_ratio"
        )

        reasons = item.get(
            "reason",
            []
        )


        # ----------------------------------------------------
        # Direction emoji
        # ----------------------------------------------------

        if direction == "LONG":

            direction_text = "🟢 LONG"

        elif direction == "SHORT":

            direction_text = "🔴 SHORT"

        else:

            direction_text = "⚪ NEUTRAL"


        # ----------------------------------------------------
        # Basic information
        # ----------------------------------------------------

        lines.append(
            f"<b>#{index} {symbol}</b>"
        )

        lines.append(
            f"Signal: {direction_text}"
        )

        lines.append(
            f"⭐ Score: <b>{score}/100</b>"
        )

        lines.append(
            f"💪 Quality: {quality}"
        )

        lines.append(
            f"💰 Price: {price}"
        )

        lines.append(
            f"📈 24H Change: {change_pct:.2f}%"
        )


        # ----------------------------------------------------
        # RSI
        # ----------------------------------------------------

        if rsi is not None:

            lines.append(
                f"📊 RSI: {rsi:.1f}"
            )


        # ----------------------------------------------------
        # Volume ratio
        # ----------------------------------------------------

        if volume_ratio is not None:

            lines.append(
                f"🔥 Volume: {volume_ratio:.1f}x"
            )


        # ----------------------------------------------------
        # Reasons
        # ----------------------------------------------------

        if reasons:

            lines.append(
                "📝 <b>Reasons:</b>"
            )

            # Maximum 4 reasons
            for reason in reasons[:4]:

                lines.append(
                    f"• {reason}"
                )


        lines.append(
            "────────────────────"
        )


    lines.append(
        "⚠️ <i>Scanner signal hai, guaranteed trade nahi.</i>"
    )

    return "\n".join(lines)
