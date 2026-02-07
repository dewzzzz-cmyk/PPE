"""Dashboard layout components."""

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.config import DEFAULT_TICKERS, TIMEFRAMES, UPDATE_INTERVAL_MS


def build_layout() -> dbc.Container:
    """Build the main dashboard layout."""
    return dbc.Container(
        fluid=True,
        className="px-3 py-2",
        style={"backgroundColor": "#1e1e2f", "minHeight": "100vh"},
        children=[
            # -- Header --
            dbc.Row(
                dbc.Col(
                    html.Div([
                        html.H2(
                            "MOEX Trading Dashboard",
                            style={"color": "#e0e0e0", "display": "inline-block"},
                        ),
                        html.Span(
                            " | Московская биржа",
                            style={"color": "#888", "fontSize": "14px"},
                        ),
                    ]),
                    width=12,
                ),
                className="mb-2",
            ),

            # -- Controls --
            dbc.Row([
                dbc.Col([
                    html.Label("Тикер", style={"color": "#aaa", "fontSize": "12px"}),
                    dcc.Dropdown(
                        id="ticker-dropdown",
                        options=[{"label": t, "value": t} for t in DEFAULT_TICKERS],
                        value=DEFAULT_TICKERS[0],
                        clearable=False,
                        style={"backgroundColor": "#2d2d44", "color": "#000"},
                    ),
                ], width=2),
                dbc.Col([
                    html.Label("Таймфрейм", style={"color": "#aaa", "fontSize": "12px"}),
                    dcc.Dropdown(
                        id="timeframe-dropdown",
                        options=[{"label": k, "value": v} for k, v in TIMEFRAMES.items()],
                        value=60,
                        clearable=False,
                        style={"backgroundColor": "#2d2d44", "color": "#000"},
                    ),
                ], width=2),
                dbc.Col([
                    html.Label("Период (дни)", style={"color": "#aaa", "fontSize": "12px"}),
                    dcc.Dropdown(
                        id="period-dropdown",
                        options=[
                            {"label": "7 дней", "value": 7},
                            {"label": "30 дней", "value": 30},
                            {"label": "90 дней", "value": 90},
                            {"label": "180 дней", "value": 180},
                            {"label": "365 дней", "value": 365},
                        ],
                        value=90,
                        clearable=False,
                        style={"backgroundColor": "#2d2d44", "color": "#000"},
                    ),
                ], width=2),
                dbc.Col([
                    html.Label(" ", style={"fontSize": "12px"}),
                    html.Div(
                        dbc.Button(
                            "Обновить", id="refresh-btn", color="primary", size="sm",
                        ),
                    ),
                ], width=1),
                dbc.Col(
                    html.Div(id="last-update", style={"color": "#666", "fontSize": "12px", "textAlign": "right", "paddingTop": "28px"}),
                    width=5,
                ),
            ], className="mb-3"),

            # -- Signal panel --
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(id="signal-card"),
                        style={"backgroundColor": "#2d2d44", "border": "1px solid #3d3d55"},
                    ),
                    width=12,
                ),
            ], className="mb-3"),

            # -- Main chart --
            dbc.Row([
                dbc.Col(
                    dcc.Loading(
                        dcc.Graph(id="main-chart", config={"displayModeBar": True, "scrollZoom": True}),
                        type="circle", color="#7c4dff",
                    ),
                    width=12,
                ),
            ], className="mb-2"),

            # -- MACD chart --
            dbc.Row([
                dbc.Col(
                    dcc.Graph(id="macd-chart", config={"displayModeBar": False}),
                    width=12,
                ),
            ], className="mb-3"),

            # -- Price table --
            dbc.Row([
                dbc.Col([
                    html.H5("Текущие цены", style={"color": "#e0e0e0"}),
                    html.Div(id="prices-table"),
                ], width=12),
            ]),

            # -- Auto-refresh --
            dcc.Interval(
                id="auto-refresh",
                interval=UPDATE_INTERVAL_MS,
                n_intervals=0,
            ),
        ],
    )
