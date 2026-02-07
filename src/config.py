"""Application configuration."""

# MOEX ISS API
MOEX_ISS_BASE = "https://iss.moex.com/iss"

# Default tickers to track
DEFAULT_TICKERS = [
    "SBER",   # Сбербанк
    "GAZP",   # Газпром
    "LKOH",   # Лукойл
    "YNDX",   # Яндекс
    "GMKN",   # Норникель
    "ROSN",   # Роснефть
    "NVTK",   # Новатэк
    "MTSS",   # МТС
    "MGNT",   # Магнит
    "PLZL",   # Полюс
]

# Timeframe mappings for MOEX ISS candles endpoint
TIMEFRAMES = {
    "1м":  1,
    "5м":  5,  # not available via ISS candles, use 10
    "10м": 10,
    "15м": 15,  # not available via ISS candles, use 10 or 60
    "1ч":  60,
    "1д":  24,
    "1н":  7,
    "1мес": 31,
}

# Dashboard
DASH_HOST = "0.0.0.0"
DASH_PORT = 8050
DASH_DEBUG = True
UPDATE_INTERVAL_MS = 30_000  # refresh every 30 seconds
