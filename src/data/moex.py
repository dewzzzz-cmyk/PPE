"""MOEX ISS API data fetcher with automatic demo fallback.

Tries the live MOEX ISS API first. If the network is unavailable,
transparently falls back to bundled demo data.
"""

import datetime as dt
import os
from typing import Optional

import pandas as pd
import requests

from src.config import MOEX_ISS_BASE

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; MOEXDashboard/1.0)",
})

_DEMO_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "demo_data")
_USE_DEMO = None  # auto-detect on first call


def _is_api_available() -> bool:
    global _USE_DEMO
    if _USE_DEMO is not None:
        return not _USE_DEMO
    try:
        r = _SESSION.get(f"{MOEX_ISS_BASE}/index.json", timeout=5)
        available = r.status_code == 200
    except Exception:
        available = False
    _USE_DEMO = not available
    if _USE_DEMO:
        print("  [INFO] MOEX API unavailable — using demo data")
    else:
        print("  [INFO] Connected to MOEX ISS API")
    return available


def _load_demo_candles(ticker: str) -> pd.DataFrame:
    path = os.path.join(_DEMO_DIR, f"{ticker}.csv")
    if not os.path.exists(path):
        return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])
    df = pd.read_csv(path, parse_dates=["datetime"])
    return df


def _load_demo_prices(tickers: list[str]) -> pd.DataFrame:
    path = os.path.join(_DEMO_DIR, "_prices.csv")
    if not os.path.exists(path):
        return pd.DataFrame(columns=["ticker", "last", "change_pct", "volume", "time"])
    df = pd.read_csv(path)
    return df[df["ticker"].isin(tickers)].reset_index(drop=True)


def fetch_candles(
    ticker: str,
    interval: int = 60,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch OHLCV candles from MOEX ISS (or demo data if unavailable)."""
    if not _is_api_available():
        return _load_demo_candles(ticker)

    if start is None:
        start = (dt.date.today() - dt.timedelta(days=180)).isoformat()
    if end is None:
        end = dt.date.today().isoformat()

    url = f"{MOEX_ISS_BASE}/engines/stock/markets/shares/securities/{ticker}/candles.json"

    all_rows = []
    cursor_start = 0

    while True:
        params = {
            "from": start,
            "till": end,
            "interval": interval,
            "start": cursor_start,
        }
        resp = _SESSION.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        candles = data.get("candles", {})
        columns = candles.get("columns", [])
        rows = candles.get("data", [])

        if not rows:
            break

        all_rows.extend(rows)
        cursor_start += len(rows)

        if len(rows) < 500:
            break

    if not all_rows:
        return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume"])

    df = pd.DataFrame(all_rows, columns=columns)

    rename_map = {
        "open": "open",
        "close": "close",
        "high": "high",
        "low": "low",
        "value": "value",
        "volume": "volume",
        "begin": "datetime",
        "end": "end_dt",
    }
    df = df.rename(columns=rename_map)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    return df[["datetime", "open", "high", "low", "close", "volume"]]


def fetch_current_prices(tickers: list[str]) -> pd.DataFrame:
    """Fetch latest market data for multiple tickers."""
    if not _is_api_available():
        return _load_demo_prices(tickers)

    url = f"{MOEX_ISS_BASE}/engines/stock/markets/shares/securities.json"
    params = {
        "iss.meta": "off",
        "securities.columns": "SECID,LAST,LASTTOPREVPRICE,VOLTODAY,TIME",
    }
    resp = _SESSION.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    securities = data.get("securities", {})
    columns = securities.get("columns", [])
    rows = securities.get("data", [])

    df = pd.DataFrame(rows, columns=columns)
    df = df.rename(columns={
        "SECID": "ticker",
        "LAST": "last",
        "LASTTOPREVPRICE": "change_pct",
        "VOLTODAY": "volume",
        "TIME": "time",
    })

    df = df[df["ticker"].isin(tickers)]
    return df.reset_index(drop=True)


def get_available_tickers(limit: int = 50) -> list[str]:
    """Get a list of actively traded share tickers on MOEX."""
    if not _is_api_available():
        return [f.replace(".csv", "") for f in os.listdir(_DEMO_DIR)
                if f.endswith(".csv") and not f.startswith("_")][:limit]

    url = f"{MOEX_ISS_BASE}/engines/stock/markets/shares/securities.json"
    params = {
        "iss.meta": "off",
        "marketdata.columns": "SECID,VOLTODAY",
    }
    resp = _SESSION.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    md = data.get("marketdata", {})
    columns = md.get("columns", [])
    rows = md.get("data", [])

    df = pd.DataFrame(rows, columns=columns)
    df = df[df["VOLTODAY"] > 0]
    df = df.sort_values("VOLTODAY", ascending=False)

    return df["SECID"].head(limit).tolist()
