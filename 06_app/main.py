"""
Entry point for the chatbot backend: uvicorn main:app --reload
"""
from api import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
