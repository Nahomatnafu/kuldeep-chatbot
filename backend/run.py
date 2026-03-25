"""Simple backend launcher for local development."""

import os

# Workaround for Windows OpenMP runtime collisions (libomp vs libiomp)
# triggered by certain transitive ML dependencies during first request.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import app

if __name__ == "__main__":
    app.app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

