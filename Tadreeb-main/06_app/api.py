"""
REST API for the chatbot (FastAPI).
Exposes POST /api/chat and GET /health, matching Frontend/src/services/chatApi.ts.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "05_generation"))
from generate_answer import generate_answer

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Tadreeb AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


def guess_organization(org: str) -> str:
    return {"iti": "ITI", "nti": "NTI", "depi": "DEPI", "itida": "ITIDA"}.get(org, "MCIT")


def format_sources(chunks: list[dict]) -> list[dict]:
    """
    chunks هنا هي نتيجة Retriever.retrieve() - كل عنصر شكله
    {"text": ..., "score": ..., "metadata": {"org", "document", "page"}}.
    """
    sources = []
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        document = meta.get("document", "unknown")
        page = meta.get("page", "?")
        sources.append({
            "id": f"{document}-p{page}",
            "title": document,
            "url": "#",
            "organization": guess_organization(meta.get("org", "")),
            "type": "document",
            "description": f"صفحة {page}",
        })
    return sources


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(request: ChatRequest):
    result = generate_answer(request.message)
    return {
        "answer": result["answer"],
        "sources": format_sources(result["sources"]),
        "suggested_questions": [],
    }
