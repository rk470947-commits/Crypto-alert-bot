  1	# ============================================================
     2	# config.py - BOT KI SETTINGS (Settings / Configuration file)
     3	# ------------------------------------------------------------
     4	# Is file me hum wo sab likhte hain jo bot ko chalane ke liye
     5	# chahiye: Telegram token, chat ID, kitni baar scan karna hai,
     6	# kitne coin dikhane hain, wagairah.
     7	# ============================================================
     8	
     9	# --- Telegram Bot Token ---
    10	# Jab aap BotFather se bot banayenge tab aapko ek "token" milega.
    11	# Wo token neeche paste karna hai. (Quotes ke andar rakho)
    12	TELEGRAM_BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
    13	
    14	# --- Telegram Chat ID ---
    15	# Ye aapke Telegram account / group ki unique ID hai.
    16	# Isko aap @userinfobot ya @RawDataBot se nikal sakte ho.
    17	TELEGRAM_CHAT_ID = "PASTE_YOUR_CHAT_ID_HERE"
    18	
    19	# --- Kitni baar scan karna hai (seconds me) ---
    20	# 15 minute = 900 seconds. Har 900 second pe bot naye top 5 coins bhejega.
    21	SCAN_INTERVAL_SECONDS = 900
    22	
    23	# --- Kitne top coin dikhane hain ---
    24	TOP_N_COINS = 5
    25	
    26	# --- Minimum volume filter (24h volume in USDT) ---
    27	# Bohot chote coins ko hatane ke liye - jinka 24h volume kam hai
    28	# unko skip karenge. Ye filter change kar sakte ho.
    29	MIN_24H_VOLUME_USDT = 5_000_000   # 50 lakh USDT (5 million)
    30	
    31	# --- Binance API base URL ---
    32	# Ye public API hai, koi key/secret nahi chahiye market data ke liye
    33	BINANCE_BASE_URL = "https://api.binance.com"
    34	
    35	# --- Klines (candles) kitne maangne hain scoring ke liye ---
    36	# Recent candles se hum price change, RSI, volatility nikalte hain
    37	KLINE_LIMIT = 30   # last 30 fifteen-minute candles
    38	
    39	# --- Safe mode (testing ke liye) ---
    40	# Agar True hai to bot Telegram pe message nahi bhejega,
    41	# sirf terminal me print karega. Pehli baar True rakho.
    42	DRY_RUN = True
