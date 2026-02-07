"""MOEX ISS API data fetcher.

Provides candle (OHLCV) and market data from the Moscow Exchange
using the public ISS API (no auth required, ~15 min delay).
"""

import datetime as dt
from typing import Optional

import pandas as pd
import requests

from src.config import MOEX_ISS_BASE


def fetch_candles(
    ticker: str,
    interval: int = 60,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch OHLCV candles from MOEX ISS.

    Args:
        ticker: Security ticker (e.g. "SBER").
        interval: Candle interval — 1, 10, 60 (minutes), 24 (day), 7 (week), 31 (month).
        start: Start date "YYYY-MM-DD". Defaults to 6 months ago.
        end: End date "YYYY-MM-DD". Defaults to today.

    Returns:
        DataFrame with columns: open, close, high, low, volume, datetime.
    """
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
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        candles = data.get("candles", {})
        columns = candles.get("columns", [])
        rows = candles.get("data", [])

        if not rows:
            break

        all_rows.extend(rows)
        cursor_start += len(rows)

        # ISS returns max 500 rows per request
        if len(rows) < 500:
            break

    if not all_rows:
        return pd.DataFrame(columns=["open", "close", "high", "low", "volume", "datetime"])

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
    """Fetch latest market data for multiple tickers.

    Returns DataFrame with columns: ticker, last, change_pct, volume, time.
    """
    url = f"{MOEX_ISS_BASE}/engines/stock/markets/shares/securities.json"
    params = {
        "iss.meta": "off",
        "securities.columns": "SECID,LAST,LASTTOPREVPRICE,VOLTODAY,TIME",
    }
    resp = requests.get(url, params=params, timeout=15)
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
    url = f"{MOEX_ISS_BASE}/engines/stock/markets/shares/securities.json"
    params = {
        "iss.meta": "off",
        "marketdata.columns": "SECID,VOLTODAY",
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    md = data.get("marketdata", {})
    columns = md.get("columns", [])
    rows = md.get("data", [])

    df = pd.DataFrame(rows, columns=columns)
    df = df[df["VOLTODAY"] > 0]
    df = df.sort_values("VOLTODAY", ascending=False)

    return df["SECID"].head(limit).tolist()
