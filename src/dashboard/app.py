"""Dash application factory."""

import dash
import dash_bootstrap_components as dbc

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

    # Import callbacks to register them
    import src.dashboard.callbacks  # noqa: F401

    return app
