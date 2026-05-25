"""TradingView-style chart builders using dash-tvlwc."""

import dash_tvlwc
import plotly.graph_objects as go
import pandas as pd


def build_tv_candlestick(df: pd.DataFrame, ticker: str) -> dict:
    """Build TradingView Lightweight Chart config for candlestick + volume.

    Returns dict with all Tvlwc component props.
    """
    if df.empty:
        return _empty_chart_props()

    # Candlestick data — format: {time: "YYYY-MM-DD", open, high, low, close}
    candle_data = []
    for _, row in df.iterrows():
        candle_data.append({
            "time": row["datetime"].strftime("%Y-%m-%d") if hasattr(row["datetime"], "strftime")
                    else str(row["datetime"])[:10],
            "open": round(float(row["open"]), 2),
            "high": round(float(row["high"]), 2),
            "low": round(float(row["low"]), 2),
            "close": round(float(row["close"]), 2),
        })

    # Volume as histogram
    volume_data = []
    for _, row in df.iterrows():
        color = "rgba(38,166,154,0.5)" if row["close"] >= row["open"] else "rgba(239,83,80,0.5)"
        volume_data.append({
            "time": row["datetime"].strftime("%Y-%m-%d") if hasattr(row["datetime"], "strftime")
                    else str(row["datetime"])[:10],
            "value": int(row["volume"]),
            "color": color,
        })

    series_data = [candle_data, volume_data]
    series_types = ["candlestick", "histogram"]
    series_options = [
        {
            "upColor": "#26a69a",
            "downColor": "#ef5350",
            "borderUpColor": "#26a69a",
            "borderDownColor": "#ef5350",
            "wickUpColor": "#26a69a",
            "wickDownColor": "#ef5350",
        },
        {
            "priceFormat": {"type": "volume"},
            "priceScaleId": "volume",
        },
    ]

    # SMA overlays as line series
    for col, color, name in [("sma20", "#ff9800", "SMA20"), ("sma50", "#2196f3", "SMA50")]:
        if col in df.columns:
            line_data = []
            for _, row in df.iterrows():
                if pd.notna(row.get(col)):
                    line_data.append({
                        "time": row["datetime"].strftime("%Y-%m-%d") if hasattr(row["datetime"], "strftime")
                                else str(row["datetime"])[:10],
                        "value": round(float(row[col]), 2),
                    })
            if line_data:
                series_data.append(line_data)
                series_types.append("line")
                series_options.append({
                    "color": color,
                    "lineWidth": 1,
                    "priceLineVisible": False,
                    "lastValueVisible": False,
                })

    # Bollinger Bands
    for col, label in [("bb_upper", "BB+"), ("bb_lower", "BB-")]:
        if col in df.columns:
            bb_data = []
            for _, row in df.iterrows():
                if pd.notna(row.get(col)):
                    bb_data.append({
                        "time": row["datetime"].strftime("%Y-%m-%d") if hasattr(row["datetime"], "strftime")
                                else str(row["datetime"])[:10],
                        "value": round(float(row[col]), 2),
                    })
            if bb_data:
                series_data.append(bb_data)
                series_types.append("line")
                series_options.append({
                    "color": "rgba(156,39,176,0.4)",
                    "lineWidth": 1,
                    "lineStyle": 2,  # dashed
                    "priceLineVisible": False,
                    "lastValueVisible": False,
                })

    # Buy/Sell markers on the candlestick series (index 0)
    markers = []
    if "signal" in df.columns:
        for _, row in df.iterrows():
            if row.get("signal") == "BUY":
                markers.append({
                    "time": row["datetime"].strftime("%Y-%m-%d") if hasattr(row["datetime"], "strftime")
                            else str(row["datetime"])[:10],
                    "position": "belowBar",
                    "color": "#26a69a",
                    "shape": "arrowUp",
                    "text": "BUY",
                })
            elif row.get("signal") == "SELL":
                markers.append({
                    "time": row["datetime"].strftime("%Y-%m-%d") if hasattr(row["datetime"], "strftime")
                            else str(row["datetime"])[:10],
                    "position": "aboveBar",
                    "color": "#ef5350",
                    "shape": "arrowDown",
                    "text": "SELL",
                })

    # seriesMarkers: one list per series, markers go on series[0] (candlestick)
    series_markers = [markers] + [[] for _ in range(len(series_data) - 1)]

    chart_options = {
        "layout": {
            "background": {"type": "solid", "color": "#131722"},
            "textColor": "#d1d4dc",
        },
        "grid": {
            "vertLines": {"color": "rgba(42,46,57,0.5)"},
            "horzLines": {"color": "rgba(42,46,57,0.5)"},
        },
        "crosshair": {
            "mode": 0,
        },
        "rightPriceScale": {
            "borderColor": "rgba(197,203,206,0.3)",
        },
        "timeScale": {
            "borderColor": "rgba(197,203,206,0.3)",
            "timeVisible": True,
        },
    }

    return {
        "seriesData": series_data,
        "seriesTypes": series_types,
        "seriesOptions": series_options,
        "seriesMarkers": series_markers,
        "chartOptions": chart_options,
    }


def build_rsi_chart(df: pd.DataFrame) -> go.Figure:
    """Build RSI chart (keeping Plotly for subcharts)."""
    fig = go.Figure()

    if "rsi" not in df.columns or df.empty:
        fig.update_layout(_dark_layout())
        return fig

    fig.add_trace(go.Scatter(
        x=df["datetime"], y=df["rsi"],
        name="RSI", line=dict(color="#7c4dff", width=1.5),
    ))

    fig.add_hline(y=70, line_dash="dash", line_color="#ef5350", opacity=0.5)
    fig.add_hline(y=30, line_dash="dash", line_color="#26a69a", opacity=0.5)
    fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.05)
    fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.05)

    fig.update_layout(
        **_dark_layout(),
        height=150,
        yaxis=dict(range=[0, 100], gridcolor="#2a2e39"),
        xaxis=dict(gridcolor="#2a2e39"),
    )

    return fig


def build_macd_chart(df: pd.DataFrame) -> go.Figure:
    """Build MACD chart."""
    fig = go.Figure()

    if "macd" not in df.columns or df.empty:
        fig.update_layout(_dark_layout())
        return fig

    fig.add_trace(go.Scatter(
        x=df["datetime"], y=df["macd"],
        name="MACD", line=dict(color="#2196f3", width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=df["datetime"], y=df["macd_signal"],
        name="Signal", line=dict(color="#ff9800", width=1.5),
    ))

    colors = ["#26a69a" if v >= 0 else "#ef5350" for v in df["macd_hist"].fillna(0)]
    fig.add_trace(go.Bar(
        x=df["datetime"], y=df["macd_hist"],
        name="Hist", marker_color=colors,
    ))

    fig.update_layout(
        **_dark_layout(),
        height=150,
        yaxis=dict(gridcolor="#2a2e39"),
        xaxis=dict(gridcolor="#2a2e39"),
    )

    return fig


def _dark_layout() -> dict:
    return {
        "template": "plotly_dark",
        "margin": dict(l=50, r=20, t=10, b=20),
        "legend": dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        "paper_bgcolor": "#131722",
        "plot_bgcolor": "#131722",
        "hovermode": "x unified",
    }


def _empty_chart_props() -> dict:
    return {
        "seriesData": [[{"time": "2026-01-01", "open": 0, "high": 0, "low": 0, "close": 0}]],
        "seriesTypes": ["candlestick"],
        "seriesOptions": [{}],
        "seriesMarkers": [[]],
        "chartOptions": {
            "layout": {
                "background": {"type": "solid", "color": "#131722"},
                "textColor": "#d1d4dc",
            },
        },
    }
