"""Entry point — run the MOEX Trading Dashboard."""

from src.config import DASH_HOST, DASH_PORT, DASH_DEBUG
from src.dashboard.app import create_app

app = create_app()
server = app.server  # for gunicorn

if __name__ == "__main__":
    print(f"\n  MOEX Trading Dashboard")
    print(f"  http://localhost:{DASH_PORT}\n")
    app.run(host=DASH_HOST, port=DASH_PORT, debug=DASH_DEBUG)
