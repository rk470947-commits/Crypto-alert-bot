1	# ============================================================
     2	# telegram_bot.py - TELEGRAM PE MESSAGE BHEJNA
     3	# ------------------------------------------------------------
     4	# Ye file Telegram Bot API ko call karke message bhejti hai.
     5	# BotFather se mila hua token aur chat ID config se aata hai.
     6	# ============================================================
     7	
     8	import requests
     9	from datetime import datetime
    10	from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DRY_RUN
    11	from scoring import rate_to_emoji
    12	
    13	
    14	def send_telegram(text):
    15	    """Telegram pe ek message bhejta hai."""
    16	    if DRY_RUN:
    17	        print("=" * 70)
    18	        print("[DRY-RUN] Telegram pe ye message jaata:")
    19	        print(text)
    20	        print("=" * 70)
    21	        return True
    22	
    23	    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    24	    payload = {
    25	        "chat_id": TELEGRAM_CHAT_ID,
    26	        "text": text,
    27	        "parse_mode": "HTML",
    28	        "disable_web_page_preview": True,
    29	    }
    30	    try:
    31	        r = requests.post(url, json=payload, timeout=15)
    32	        if r.status_code == 200:
    33	            return True
    34	        print(f"[error] Telegram send failed: {r.status_code} {r.text[:200]}")
    35	        return False
    36	    except Exception as e:
    37	        print(f"[error] Telegram exception: {e}")
    38	        return False
    39	
    40	
    41	def format_alert(top_results):
    42	    """
    43	    top_results: list of dicts (score_symbol ka return)
    44	    Ek sundar HTML message banata hai jo bheja jaayega.
    45	    """
    46	    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    47	    lines = []
    48	    lines.append(f"🚨 <b>Binance Top Movers Alert</b>")
    49	    lines.append(f"🕐 <i>{now}</i>")
    50	    lines.append("")
    51	    lines.append("📊 <b>Aaj ke Top 5 potential movers:</b>\n")
    52	
    53	    for idx, r in enumerate(top_results, start=1):
    54	        em = rate_to_emoji(r["rating"])
    55	        sym = r["symbol"].replace("USDT", "/USDT")
    56	        lines.append(
    57	            f"<b>{idx}. {em} {sym}</b>\n"
    58	            f"   ⭐ Score: <b>{r['score']}</b>  |  Rating: <b>{r['rating']}</b>\n"
    59	            f"   📈 RSI: {r.get('rsi','-')}  |  "
    60	            f"15m Volatility: {r.get('vol15_pct','-')}%\n"
    61	            f"   🔥 Volume Spike: {r.get('rel_volume','-')}x  |  "
    62	            f"Signal: <i>{r['reason']}</i>"
    63	        )
    64	        lines.append("")
    65	
    66	    lines.append("⚠️ <i>Disclaimer: Ye signal guarantee nahi hai. "
    67	                 "Trading me loss ka risk hamesha hota hai. "
    68	                 "Apni research zaroor karein.</i>")
    69	    return "\n".join(lines)
