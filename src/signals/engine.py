"""Signal engine — technical indicators and trade signal generation.

Pure pandas implementation (no external TA libraries required).
"""

import numpy as np
import pandas as pd


# ─── Indicator calculations ───────────────────────────────────────────

def _sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(window=length, min_periods=length).mean()


def _ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def _rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = _ema(series, fast)
    ema_slow = _ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = _ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, histogram, signal_line


def _bbands(series: pd.Series, length: int = 20, std: float = 2.0):
    mid = _sma(series, length)
    rolling_std = series.rolling(window=length, min_periods=length).std()
    upper = mid + std * rolling_std
    lower = mid - std * rolling_std
    return lower, mid, upper


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=length, min_periods=length).mean()


# ─── Public API ───────────────────────────────────────────────────────

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add technical indicators to OHLCV DataFrame.

    Adds: SMA20, SMA50, EMA12, EMA26, RSI14, MACD, Bollinger Bands, ATR.
    """
    if df.empty or len(df) < 26:
        return df

    df = df.copy()

    # Moving Averages
    df["sma20"] = _sma(df["close"], 20)
    df["sma50"] = _sma(df["close"], 50)
    df["ema12"] = _ema(df["close"], 12)
    df["ema26"] = _ema(df["close"], 26)

    # RSI
    df["rsi"] = _rsi(df["close"], 14)

    # MACD
    macd_line, macd_hist, macd_sig = _macd(df["close"], 12, 26, 9)
    df["macd"] = macd_line
    df["macd_hist"] = macd_hist
    df["macd_signal"] = macd_sig

    # Bollinger Bands
    bb_lower, bb_mid, bb_upper = _bbands(df["close"], 20, 2.0)
    df["bb_lower"] = bb_lower
    df["bb_mid"] = bb_mid
    df["bb_upper"] = bb_upper

    # ATR (for stop-loss)
    df["atr"] = _atr(df["high"], df["low"], df["close"], 14)

    # Volume SMA
    df["vol_sma20"] = _sma(df["volume"], 20)

    return df


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Generate buy/sell signals based on multi-indicator confluence.

    Scoring system (each +1 point):
      BUY:  RSI < 35, MACD bullish crossover, price near lower BB, volume spike
      SELL: RSI > 65, MACD bearish crossover, price near upper BB

    Signal strength: score out of max possible points.
    """
    if df.empty or "rsi" not in df.columns:
        df["signal"] = None
        df["score"] = 0
        return df

    df = df.copy()
    df["buy_score"] = 0
    df["sell_score"] = 0

    # RSI
    df.loc[df["rsi"] < 35, "buy_score"] += 1
    df.loc[df["rsi"] > 65, "sell_score"] += 1

    # MACD crossover
    if "macd" in df.columns and "macd_signal" in df.columns:
        macd_cross_up = (df["macd"] > df["macd_signal"]) & (df["macd"].shift(1) <= df["macd_signal"].shift(1))
        macd_cross_down = (df["macd"] < df["macd_signal"]) & (df["macd"].shift(1) >= df["macd_signal"].shift(1))
        df.loc[macd_cross_up, "buy_score"] += 1
        df.loc[macd_cross_down, "sell_score"] += 1

    # Bollinger Bands proximity
    if "bb_lower" in df.columns and "bb_upper" in df.columns:
        bb_range = df["bb_upper"] - df["bb_lower"]
        near_lower = (df["close"] - df["bb_lower"]) < (bb_range * 0.1)
        near_upper = (df["bb_upper"] - df["close"]) < (bb_range * 0.1)
        df.loc[near_lower, "buy_score"] += 1
        df.loc[near_upper, "sell_score"] += 1

    # Volume spike (> 1.5x 20-period average)
    if "vol_sma20" in df.columns:
        vol_spike = df["volume"] > (df["vol_sma20"] * 1.5)
        df.loc[vol_spike, "buy_score"] += 1
        df.loc[vol_spike, "sell_score"] += 1

    # Generate signal
    df["signal"] = None
    df.loc[df["buy_score"] >= 2, "signal"] = "BUY"
    df.loc[df["sell_score"] >= 2, "signal"] = "SELL"

    # Where both are >= 2, pick the stronger one
    both = (df["buy_score"] >= 2) & (df["sell_score"] >= 2)
    df.loc[both & (df["buy_score"] > df["sell_score"]), "signal"] = "BUY"
    df.loc[both & (df["sell_score"] > df["buy_score"]), "signal"] = "SELL"
    df.loc[both & (df["buy_score"] == df["sell_score"]), "signal"] = None

    df["score"] = df[["buy_score", "sell_score"]].max(axis=1)

    return df


def get_latest_signal(df: pd.DataFrame) -> dict:
    """Get the latest signal from the DataFrame.

    Returns dict with: signal, score, rsi, macd_status, bb_status, price, atr.
    """
    if df.empty:
        return {"signal": None}

    last = df.iloc[-1]

    macd_status = None
    if "macd" in df.columns and "macd_signal" in df.columns:
        if pd.notna(last.get("macd")) and pd.notna(last.get("macd_signal")):
            macd_status = "bullish" if last["macd"] > last["macd_signal"] else "bearish"

    bb_status = None
    if "bb_lower" in df.columns and "bb_upper" in df.columns:
        if pd.notna(last.get("bb_lower")) and pd.notna(last.get("bb_upper")):
            bb_range = last["bb_upper"] - last["bb_lower"]
            if bb_range > 0:
                position = (last["close"] - last["bb_lower"]) / bb_range
                if position < 0.2:
                    bb_status = "near_lower"
                elif position > 0.8:
                    bb_status = "near_upper"
                else:
                    bb_status = "middle"

    stop_loss = None
    take_profit = None
    if pd.notna(last.get("atr")):
        atr = last["atr"]
        if last.get("signal") == "BUY":
            stop_loss = round(last["close"] - 2 * atr, 2)
            take_profit = round(last["close"] + 3 * atr, 2)
        elif last.get("signal") == "SELL":
            stop_loss = round(last["close"] + 2 * atr, 2)
            take_profit = round(last["close"] - 3 * atr, 2)

    return {
        "signal": last.get("signal"),
        "score": int(last.get("score", 0)),
        "price": last.get("close"),
        "rsi": round(last["rsi"], 1) if pd.notna(last.get("rsi")) else None,
        "macd_status": macd_status,
        "bb_status": bb_status,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "atr": round(last["atr"], 2) if pd.notna(last.get("atr")) else None,
        "datetime": str(last.get("datetime", "")),
    }
