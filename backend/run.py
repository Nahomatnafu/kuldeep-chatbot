"""Simple backend launcher for local development."""

import os

import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)

