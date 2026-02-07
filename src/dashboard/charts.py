"""Chart builders for the dashboard."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def build_candlestick_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Build a full trading chart: candlesticks + volume + indicators.

    Layout:
      Row 1 (60%): Candlesticks + MA + Bollinger Bands + signals
      Row 2 (20%): Volume
      Row 3 (20%): RSI
    """
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=(f"{ticker}", "Volume", "RSI"),
    )

    # -- Row 1: Candlesticks --
    fig.add_trace(
        go.Candlestick(
            x=df["datetime"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="OHLC",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )

    # SMA 20
    if "sma20" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["datetime"], y=df["sma20"],
                name="SMA 20", line=dict(color="#ff9800", width=1),
            ),
            row=1, col=1,
        )

    # SMA 50
    if "sma50" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["datetime"], y=df["sma50"],
                name="SMA 50", line=dict(color="#2196f3", width=1),
            ),
            row=1, col=1,
        )

    # Bollinger Bands
    if "bb_upper" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["datetime"], y=df["bb_upper"],
                name="BB Upper", line=dict(color="#9c27b0", width=1, dash="dash"),
                showlegend=False,
            ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df["datetime"], y=df["bb_lower"],
                name="BB Lower", line=dict(color="#9c27b0", width=1, dash="dash"),
                fill="tonexty", fillcolor="rgba(156,39,176,0.05)",
                showlegend=False,
            ),
            row=1, col=1,
        )

    # Buy/Sell signals as markers
    if "signal" in df.columns:
        buys = df[df["signal"] == "BUY"]
        sells = df[df["signal"] == "SELL"]

        if not buys.empty:
            fig.add_trace(
                go.Scatter(
                    x=buys["datetime"], y=buys["low"] * 0.998,
                    mode="markers", name="BUY",
                    marker=dict(symbol="triangle-up", size=12, color="#26a69a"),
                ),
                row=1, col=1,
            )
        if not sells.empty:
            fig.add_trace(
                go.Scatter(
                    x=sells["datetime"], y=sells["high"] * 1.002,
                    mode="markers", name="SELL",
                    marker=dict(symbol="triangle-down", size=12, color="#ef5350"),
                ),
                row=1, col=1,
            )

    # -- Row 2: Volume --
    colors = [
        "#26a69a" if c >= o else "#ef5350"
        for c, o in zip(df["close"], df["open"])
    ]
    fig.add_trace(
        go.Bar(
            x=df["datetime"], y=df["volume"],
            name="Volume", marker_color=colors, showlegend=False,
        ),
        row=2, col=1,
    )

    # Volume SMA
    if "vol_sma20" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["datetime"], y=df["vol_sma20"],
                name="Vol SMA20", line=dict(color="#ff9800", width=1),
                showlegend=False,
            ),
            row=2, col=1,
        )

    # -- Row 3: RSI --
    if "rsi" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["datetime"], y=df["rsi"],
                name="RSI", line=dict(color="#7c4dff", width=1.5),
            ),
            row=3, col=1,
        )
        # Overbought / Oversold zones
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)
        fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.05, row=3, col=1)
        fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.05, row=3, col=1)

    # -- Layout --
    fig.update_layout(
        template="plotly_dark",
        height=750,
        margin=dict(l=50, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_rangeslider_visible=False,
        xaxis3_rangeslider_visible=False,
        hovermode="x unified",
        paper_bgcolor="#1e1e2f",
        plot_bgcolor="#1e1e2f",
    )

    fig.update_yaxes(gridcolor="#2d2d44", row=1, col=1)
    fig.update_yaxes(gridcolor="#2d2d44", row=2, col=1)
    fig.update_yaxes(gridcolor="#2d2d44", range=[0, 100], row=3, col=1)
    fig.update_xaxes(gridcolor="#2d2d44")

    return fig


def build_macd_chart(df: pd.DataFrame) -> go.Figure:
    """Build a standalone MACD chart."""
    fig = go.Figure()

    if "macd" not in df.columns:
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
        name="Histogram", marker_color=colors,
    ))

    fig.update_layout(
        template="plotly_dark",
        height=200,
        margin=dict(l=50, r=20, t=10, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor="#1e1e2f",
        plot_bgcolor="#1e1e2f",
        hovermode="x unified",
    )
    fig.update_yaxes(gridcolor="#2d2d44")
    fig.update_xaxes(gridcolor="#2d2d44")

    return fig
