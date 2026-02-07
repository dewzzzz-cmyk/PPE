"""Generate a static preview of the dashboard charts."""

import pandas as pd
import numpy as np
from src.signals.engine import add_indicators, generate_signals
from src.dashboard.charts import build_candlestick_chart, build_macd_chart

# Simulate realistic SBER price data
np.random.seed(7)
n = 200
dates = pd.date_range("2025-11-01", periods=n, freq="h")

# Trending price with mean-reversion
price = 260.0
prices = []
for i in range(n):
    price += np.random.randn() * 1.5 + 0.05 * np.sin(i / 20)
    prices.append(max(price, 200))

close = np.array(prices)
df = pd.DataFrame({
    "datetime": dates,
    "open": close - np.random.rand(n) * 1.5,
    "high": close + np.abs(np.random.randn(n)) * 1.2,
    "low": close - np.abs(np.random.randn(n)) * 1.2,
    "close": close,
    "volume": np.random.randint(100000, 800000, n),
})

# Add some volume spikes
df.loc[50:53, "volume"] = 2_000_000
df.loc[120:123, "volume"] = 1_800_000

df = add_indicators(df)
df = generate_signals(df)

# Main chart
fig = build_candlestick_chart(df, "SBER")
fig.update_layout(width=1400, height=800)
fig.write_image("/home/user/PPE/preview_main.png", scale=2)

# MACD chart
macd_fig = build_macd_chart(df)
macd_fig.update_layout(width=1400, height=250)
macd_fig.write_image("/home/user/PPE/preview_macd.png", scale=2)

print("Previews saved!")
