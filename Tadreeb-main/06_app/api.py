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
from pydantic import BaseModel, Field

app = FastAPI(title="Tadreeb AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessageTurn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    language: str | None = "ar"
    history: list[MessageTurn] | None = Field(default_factory=list)


def guess_organization(org: str) -> str:
    return {"iti": "ITI", "nti": "NTI", "depi": "DEPI", "itida": "ITIDA"}.get(org, "MCIT")


def format_sources(chunks: list[dict]) -> list[dict]:
    sources = []
    for chunk in chunks:
        doc_name = chunk.get("document", "Source Document")
        page_num = chunk.get("page", 1)
        sources.append({
            "id": f"{doc_name}-p{page_num}",
            "title": chunk.get("title", doc_name),
            "url": chunk.get("url", "#"),
            "organization": guess_organization(chunk.get("org", "")),
            "type": "official" if "web" in doc_name else "document",
            "description": f"صفحة {page_num}" if "web" not in doc_name else "الموقع الرسمي",
        })
    return sources


@app.on_event("startup")
def startup_vector_db_check():
    """If a new collaborator clones the project and ChromaDB is empty, automatically index bundled chunks."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "03_rag_pipeline" / "embeddings"))
        from vector_db_config import get_collection
        col = get_collection()
        if col.count() == 0:
            print("⚡ [Auto-Bootstrap] ChromaDB is empty. Indexing bundled chunks from 02_data/04_chunks/...")
            import subprocess
            script_path = Path(__file__).resolve().parent.parent / "03_rag_pipeline" / "embeddings" / "embed_and_store.py"
            subprocess.run([sys.executable, str(script_path)])
    except Exception as e:
        print(f"Notice during startup bootstrap: {e}")


@app.get("/health")
def health():
    return {"status": "ok"}



@app.post("/api/chat")
def chat(request: ChatRequest):
    history_list = [h.model_dump() for h in (request.history or [])]
    result = generate_answer(request.message, history=history_list)
    return {
        "answer": result["answer"],
        "sources": format_sources(result.get("sources", [])),
        "suggested_questions": [],
    }
