"""Entry point — run the MOEX Trading Dashboard."""

import os

from src.dashboard.app import create_app

app = create_app()
server = app.server  # for gunicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DASH_DEBUG", "true").lower() == "true"
    print(f"\n  MOEX Trading Dashboard")
    print(f"  http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
