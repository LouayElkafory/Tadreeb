"""
Production ASGI entry point.

06_app/ can't be used as a dotted Python module path (identifiers can't start
with a digit), so `uvicorn 06_app.main:app` is not valid. This file lets any
standard Python host run the backend from the project root instead:

    uvicorn server:app --host 0.0.0.0 --port $PORT

It only adds 06_app to sys.path and re-exports its FastAPI `app` - no logic
lives here.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "06_app"))

from api import app  # noqa: E402

__all__ = ["app"]
