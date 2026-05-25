"""Dash application factory."""

import os
import dash
import dash_bootstrap_components as dbc
from flask import send_file

from src.dashboard.layout import build_layout


def create_app() -> dash.Dash:
    """Create and configure the Dash application."""
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.DARKLY],
        title="MOEX Trading Dashboard",
        update_title="Загрузка...",
    )

    app.layout = build_layout()

    import src.dashboard.callbacks  # noqa: F401

    widget_path = os.path.join(os.path.dirname(__file__), "..", "..", "widget.html")

    @app.server.route("/tradingview")
    def tradingview_widget():
        return send_file(os.path.abspath(widget_path))

    return app
