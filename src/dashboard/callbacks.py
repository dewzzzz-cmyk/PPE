"""Dashboard callbacks — wiring data to UI."""

import datetime as dt

import dash_bootstrap_components as dbc
from dash import Input, Output, callback, html
import pandas as pd

from src.data.moex import fetch_candles, fetch_current_prices
from src.signals.engine import add_indicators, generate_signals, get_latest_signal
from src.dashboard.charts import build_candlestick_chart, build_macd_chart
from src.config import DEFAULT_TICKERS


@callback(
    Output("main-chart", "figure"),
    Output("macd-chart", "figure"),
    Output("signal-card", "children"),
    Output("last-update", "children"),
    Input("ticker-dropdown", "value"),
    Input("timeframe-dropdown", "value"),
    Input("period-dropdown", "value"),
    Input("refresh-btn", "n_clicks"),
    Input("auto-refresh", "n_intervals"),
)
def update_chart(ticker, interval, period_days, _btn, _n):
    """Fetch data, compute indicators, update chart + signal panel."""
    start = (dt.date.today() - dt.timedelta(days=period_days)).isoformat()
    end = dt.date.today().isoformat()

    try:
        df = fetch_candles(ticker, interval=interval, start=start, end=end)
    except Exception:
        df = pd.DataFrame()

    if df.empty:
        import plotly.graph_objects as go
        empty_fig = go.Figure()
        empty_fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#1e1e2f",
            plot_bgcolor="#1e1e2f",
            annotations=[dict(text="Нет данных", x=0.5, y=0.5, showarrow=False, font=dict(size=24, color="#888"))],
        )
        return empty_fig, empty_fig, html.Div("Нет данных", style={"color": "#888"}), ""

    df = add_indicators(df)
    df = generate_signals(df)

    main_fig = build_candlestick_chart(df, ticker)
    macd_fig = build_macd_chart(df)

    sig = get_latest_signal(df)
    signal_panel = _build_signal_panel(sig, ticker)

    now = dt.datetime.now().strftime("%H:%M:%S")
    update_text = f"Обновлено: {now}"

    return main_fig, macd_fig, signal_panel, update_text


@callback(
    Output("prices-table", "children"),
    Input("auto-refresh", "n_intervals"),
    Input("refresh-btn", "n_clicks"),
)
def update_prices(_n, _btn):
    """Update the prices table."""
    try:
        df = fetch_current_prices(DEFAULT_TICKERS)
    except Exception:
        return html.Div("Ошибка загрузки цен", style={"color": "#ef5350"})

    if df.empty:
        return html.Div("Нет данных", style={"color": "#888"})

    rows = []
    for _, row in df.iterrows():
        change = row.get("change_pct")
        if pd.notna(change) and change is not None:
            change_val = float(change)
            color = "#26a69a" if change_val >= 0 else "#ef5350"
            sign = "+" if change_val >= 0 else ""
            change_str = f"{sign}{change_val:.2f}%"
        else:
            color = "#888"
            change_str = "—"

        last_price = row.get("last")
        price_str = f"{last_price:.2f}" if pd.notna(last_price) else "—"

        volume = row.get("volume")
        vol_str = f"{int(volume):,}".replace(",", " ") if pd.notna(volume) else "—"

        rows.append(
            html.Tr([
                html.Td(row["ticker"], style={"color": "#e0e0e0", "fontWeight": "bold"}),
                html.Td(price_str, style={"color": "#e0e0e0"}),
                html.Td(change_str, style={"color": color, "fontWeight": "bold"}),
                html.Td(vol_str, style={"color": "#aaa"}),
                html.Td(row.get("time", "—"), style={"color": "#666"}),
            ])
        )

    table = dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Тикер", style={"color": "#aaa"}),
                html.Th("Цена", style={"color": "#aaa"}),
                html.Th("Изм. %", style={"color": "#aaa"}),
                html.Th("Объём", style={"color": "#aaa"}),
                html.Th("Время", style={"color": "#aaa"}),
            ])),
            html.Tbody(rows),
        ],
        bordered=False, dark=True, hover=True, size="sm",
        style={"backgroundColor": "#1e1e2f"},
    )
    return table


def _build_signal_panel(sig: dict, ticker: str):
    """Build the signal info panel."""
    signal = sig.get("signal")
    if signal is None:
        signal_text = "НЕЙТРАЛЬНО"
        signal_color = "#888"
        signal_icon = "—"
    elif signal == "BUY":
        signal_text = "ПОКУПКА"
        signal_color = "#26a69a"
        signal_icon = "▲"
    else:
        signal_text = "ПРОДАЖА"
        signal_color = "#ef5350"
        signal_icon = "▼"

    score = sig.get("score", 0)
    rsi = sig.get("rsi")
    macd_status = sig.get("macd_status", "—")
    bb_status = sig.get("bb_status", "—")
    price = sig.get("price")
    stop = sig.get("stop_loss")
    take = sig.get("take_profit")

    bb_labels = {
        "near_lower": "у нижней границы",
        "near_upper": "у верхней границы",
        "middle": "в середине",
        None: "—",
    }
    macd_labels = {
        "bullish": "бычий",
        "bearish": "медвежий",
        None: "—",
    }

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span(f"{signal_icon} ", style={"fontSize": "28px", "color": signal_color}),
                    html.Span(f"{signal_text}", style={"fontSize": "24px", "fontWeight": "bold", "color": signal_color}),
                    html.Span(f"  {ticker}", style={"fontSize": "18px", "color": "#aaa", "marginLeft": "10px"}),
                ]),
                html.Div(f"Сила сигнала: {score}/4", style={"color": "#aaa", "fontSize": "13px"}),
            ], width=3),
            dbc.Col([
                html.Div(f"Цена: {price:.2f} ₽" if price else "Цена: —", style={"color": "#e0e0e0"}),
                html.Div(f"RSI: {rsi}" if rsi else "RSI: —", style={"color": "#e0e0e0"}),
            ], width=2),
            dbc.Col([
                html.Div(f"MACD: {macd_labels.get(macd_status, macd_status)}", style={"color": "#e0e0e0"}),
                html.Div(f"BB: {bb_labels.get(bb_status, bb_status)}", style={"color": "#e0e0e0"}),
            ], width=2),
            dbc.Col([
                html.Div(
                    f"Стоп-лосс: {stop:.2f} ₽" if stop else "Стоп-лосс: —",
                    style={"color": "#ef5350"},
                ),
                html.Div(
                    f"Тейк-профит: {take:.2f} ₽" if take else "Тейк-профит: —",
                    style={"color": "#26a69a"},
                ),
            ], width=3),
            dbc.Col([
                html.Div(
                    sig.get("datetime", ""),
                    style={"color": "#666", "fontSize": "11px", "textAlign": "right"},
                ),
            ], width=2),
        ]),
    ])
