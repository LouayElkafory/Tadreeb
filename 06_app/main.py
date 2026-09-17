"""
Entry point for the chatbot backend.

Dev:        uvicorn main:app --reload   (run from inside 06_app/)
Production: uvicorn server:app          (run from the project root - see ../server.py)
            or: python main.py          (reads HOST / PORT from the environment)
"""
import os

from api import app

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
