"""
REST API for the chatbot (FastAPI).
Exposes POST /api/chat and GET /health, matching Frontend/src/services/chatApi.ts.
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# Load environment variables from the project root .env (independent of any
# other module's import order, so config below is always available).
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except Exception:
    pass

sys.path.insert(0, str(PROJECT_ROOT / "05_generation"))
from generate_answer import generate_answer

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Tadreeb AI Backend")

# Comma-separated list of allowed frontend origins, e.g.:
#   FRONTEND_ORIGIN=https://tadreeb.vercel.app,http://localhost:5173
# Credentials are intentionally never combined with a wildcard origin - the API
# is a stateless JSON endpoint (no cookies), so allow_credentials stays False.
_raw_origins = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
ALLOWED_ORIGINS = [origin.strip() for origin in _raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Automatic ChromaDB bootstrap indexing is a development/setup convenience only.
# It must stay disabled by default in production (cold-start indexing is slow
# and can run on every restart if the vector store isn't on persistent storage).
AUTO_INDEX = os.getenv("AUTO_INDEX", "false").strip().lower() == "true"


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
    """Dev/setup convenience: if AUTO_INDEX=true and ChromaDB is empty, index the
    bundled chunks automatically. Disabled by default - production deployments
    should index once (e.g. via `python embed_and_store.py`) and set AUTO_INDEX=false,
    especially when the vector store path isn't backed by a persistent volume."""
    if not AUTO_INDEX:
        return
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "03_rag_pipeline" / "embeddings"))
        from vector_db_config import get_collection
        col = get_collection()
        if col.count() == 0:
            print("[Auto-Bootstrap] ChromaDB is empty. Indexing bundled chunks from 02_data/04_chunks/...")
            import subprocess
            script_path = PROJECT_ROOT / "03_rag_pipeline" / "embeddings" / "embed_and_store.py"
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
