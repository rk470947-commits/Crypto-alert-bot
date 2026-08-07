# ============================================================
# config.py - BOT KI SETTINGS (Settings / Configuration file)
# ------------------------------------------------------------
# Is file me hum wo sab likhte hain jo bot ko chalane ke liye
# chahiye: Telegram token, chat ID, kitni baar scan karna hai,
# kitne coin dikhane hain, wagairah.
# ============================================================

# --- Telegram Bot Token ---
# Jab aap BotFather se bot banayenge tab aapko ek "token" milega.
# Wo token neeche paste karna hai. (Quotes ke andar rakho)
TELEGRAM_BOT_TOKEN = "8826997291:AAHVew4uPHpJnAJRKhzFcmWY_LL8vhmigaE"

# --- Telegram Chat ID ---
# Ye aapke Telegram account / group ki unique ID hai.
# Isko aap @userinfobot ya @RawDataBot se nikal sakte ho.
TELEGRAM_CHAT_ID = "5891462320"

# --- Kitni baar scan karna hai (seconds me) ---
# 15 minute = 900 seconds. Har 900 second pe bot naye top 5 coins bhejega.
SCAN_INTERVAL_SECONDS = 900

# --- Kitne top coin dikhane hain ---
TOP_N_COINS = 5

# --- Minimum volume filter (24h volume in USDT) ---
# Bohot chote coins ko hatane ke liye - jinka 24h volume kam hai
# unko skip karenge. Ye filter change kar sakte ho.
MIN_24H_VOLUME_USDT = 5_000_000   # 50 lakh USDT (5 million)

# --- Binance API base URL ---
# Ye public API hai, koi key/secret nahi chahiye market data ke liye
BINANCE_BASE_URL = "https://api.binance.com"

# --- Klines (candles) kitne maangne hain scoring ke liye ---
# Recent candles se hum price change, RSI, volatility nikalte hain
KLINE_LIMIT = 30   # last 30 fifteen-minute candles

# --- Safe mode (testing ke liye) ---
# Agar True hai to bot Telegram pe message nahi bhejega,
# sirf terminal me print karega. Pehli baar True rakho.
DRY_RUN = False
