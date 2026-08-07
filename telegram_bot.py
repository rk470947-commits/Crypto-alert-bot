# ============================================================
# telegram_bot.py - TELEGRAM PE MESSAGE BHEJNA
# ------------------------------------------------------------
# Ye file Telegram Bot API ko call karke message bhejti hai.
# BotFather se mila hua token aur chat ID config se aata hai.
# ============================================================

import requests
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DRY_RUN
from scoring import rate_to_emoji


def send_telegram(text):
    """Telegram pe ek message bhejta hai."""
    if DRY_RUN:
        print("=" * 70)
        print("[DRY-RUN] Telegram pe ye message jaata:")
        print(text)
        print("=" * 70)
        return True

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            return True
        print(f"[error] Telegram send failed: {r.status_code} {r.text[:200]}")
        return False
    except Exception as e:
        print(f"[error] Telegram exception: {e}")
        return False


def format_alert(top_results):
    """
    top_results: list of dicts (score_symbol ka return)
    Ek sundar HTML message banata hai jo bheja jaayega.
    """
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = []
    lines.append(f"🚨 <b>Binance Top Movers Alert</b>")
    lines.append(f"🕐 <i>{now}</i>")
    lines.append("")
    lines.append("📊 <b>Aaj ke Top 5 potential movers:</b>\n")

    for idx, r in enumerate(top_results, start=1):
        em = rate_to_emoji(r["rating"])
        sym = r["symbol"].replace("USDT", "/USDT")
        lines.append(
            f"<b>{idx}. {em} {sym}</b>\n"
            f"   ⭐ Score: <b>{r['score']}</b>  |  Rating: <b>{r['rating']}</b>\n"
            f"   📈 RSI: {r.get('rsi','-')}  |  "
            f"15m Volatility: {r.get('vol15_pct','-')}%\n"
            f"   🔥 Volume Spike: {r.get('rel_volume','-')}x  |  "
            f"Signal: <i>{r['reason']}</i>"
        )
        lines.append("")

    lines.append("⚠️ <i>Disclaimer: Ye signal guarantee nahi hai. "
                 "Trading me loss ka risk hamesha hota hai. "
                 "Apni research zaroor karein.</i>")
    return "\n".join(lines)
