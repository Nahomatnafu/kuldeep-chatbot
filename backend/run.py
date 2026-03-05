"""
run.py — AV-safe backend launcher
Stubs out pygments (only needed for httpx CLI formatting, never at runtime)
before the import chain triggers it, then starts the Flask app normally.
"""
import sys
from unittest.mock import MagicMock

sys.modules.setdefault("pygments", MagicMock())
sys.modules.setdefault("pygments.lexers", MagicMock())
sys.modules.setdefault("pygments.formatters", MagicMock())

import app  # noqa: E402  — must come after the stubs

if __name__ == "__main__":
    app.app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

