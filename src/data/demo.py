"""Generate realistic demo data for offline/demo mode."""

import numpy as np
import pandas as pd
import json
import os

DEMO_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "demo_data")


def _generate_ohlcv(ticker: str, base_price: float, volatility: float, n: int = 500) -> pd.DataFrame:
    np.random.seed(hash(ticker) % 2**31)
    dates = pd.date_range(end=pd.Timestamp.now().normalize(), periods=n, freq="h")

    trend = np.cumsum(np.random.randn(n) * volatility + 0.01 * np.sin(np.arange(n) / 30))
    close = base_price + trend
    close = np.maximum(close, base_price * 0.5)

    high = close + np.abs(np.random.randn(n)) * volatility * 0.8
    low = close - np.abs(np.random.randn(n)) * volatility * 0.8
    opn = close + np.random.randn(n) * volatility * 0.3

    base_vol = np.random.randint(50000, 500000, n).astype(float)
    # Volume spikes
    for i in np.random.choice(n, size=n // 20, replace=False):
        base_vol[i] *= np.random.uniform(2.5, 5.0)

    return pd.DataFrame({
        "datetime": dates,
        "open": np.round(opn, 2),
        "high": np.round(high, 2),
        "low": np.round(low, 2),
        "close": np.round(close, 2),
        "volume": base_vol.astype(int),
    })


TICKERS = {
    "SBER": (305.0, 3.0),
    "GAZP": (165.0, 2.5),
    "LKOH": (7200.0, 80.0),
    "YNDX": (4100.0, 50.0),
    "GMKN": (145.0, 2.0),
    "ROSN": (530.0, 6.0),
    "NVTK": (1050.0, 12.0),
    "MTSS": (310.0, 3.5),
    "MGNT": (5400.0, 60.0),
    "PLZL": (18500.0, 200.0),
}


def generate_all():
    os.makedirs(DEMO_DIR, exist_ok=True)

    for ticker, (base, vol) in TICKERS.items():
        df = _generate_ohlcv(ticker, base, vol)
        path = os.path.join(DEMO_DIR, f"{ticker}.csv")
        df.to_csv(path, index=False)
        print(f"  {ticker}: {len(df)} candles -> {path}")

    # Generate current prices snapshot
    prices = []
    for ticker, (base, vol) in TICKERS.items():
        df = _generate_ohlcv(ticker, base, vol, n=10)
        last = df.iloc[-1]
        prev = df.iloc[-2]
        change = round((last["close"] - prev["close"]) / prev["close"] * 100, 2)
        prices.append({
            "ticker": ticker,
            "last": last["close"],
            "change_pct": change,
            "volume": int(last["volume"]),
            "time": "14:32:00",
        })
    pd.DataFrame(prices).to_csv(os.path.join(DEMO_DIR, "_prices.csv"), index=False)
    print(f"  Prices snapshot -> _prices.csv")


if __name__ == "__main__":
    print("Generating demo data...")
    generate_all()
    print("Done!")
