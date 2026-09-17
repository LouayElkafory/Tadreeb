"""
FastAPI Test Server for Faiss RAG Pipeline
Run: python test_api.py
Access: http://localhost:8001/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
from pathlib import Path

# Import the Faiss RAG pipeline
from faiss_rag_pipeline import setup_faiss_rag, FaissRAG

# ============================================================================
# INITIALIZE
# ============================================================================

app = FastAPI(title="Tadreeb Faiss RAG Test API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG instance
rag: Optional[FaissRAG] = None


# ============================================================================
# DATA MODELS
# ============================================================================

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class SourceMetadata(BaseModel):
    org: str
    document: str
    page: int
    chunk_index: int


class RetrievedChunk(BaseModel):
    text: str
    score: float
    metadata: SourceMetadata


class ChatResponse(BaseModel):
    answer: str
    sources: list[RetrievedChunk]
    chunk_count: int
    avg_score: float


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize Faiss RAG on startup."""
    global rag

    print("\n" + "="*80)
    print("🚀 INITIALIZING FAISS RAG PIPELINE")
    print("="*80)

    pdf_path = "D:/project/Tadreeb-main/Tadreeb-main/Tadreeb-updated-tadreeb (1)/Tadreeb-updated-tadreeb/Tadreeb-main/02_data/01_raw/nti/official/NTI_HireReady_Program_Guidelines.pdf"

    try:
        rag = setup_faiss_rag(pdf_path)
        print("\n✅ RAG Pipeline Ready!")
    except Exception as e:
        print(f"\n❌ Failed to initialize RAG: {e}")
        raise


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Tadreeb Faiss RAG Test",
        "rag_ready": rag is not None
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with Faiss RAG retrieval."""
    global rag

    if rag is None:
        return ChatResponse(
            answer="RAG pipeline not ready",
            sources=[],
            chunk_count=0,
            avg_score=0.0
        )

    query = request.message.strip()

    if not query:
        return ChatResponse(
            answer="Please provide a question",
            sources=[],
            chunk_count=0,
            avg_score=0.0
        )

    # Retrieve chunks
    retrieved = rag.retrieve(query, top_k=3)

    # Format response
    sources = [
        RetrievedChunk(
            text=chunk["text"],
            score=chunk["score"],
            metadata=SourceMetadata(**chunk["metadata"])
        )
        for chunk in retrieved
    ]

    # Build answer from sources
    if sources:
        answer = f"Found {len(sources)} relevant chunks:\n\n"
        for i, source in enumerate(sources, 1):
            answer += f"{i}. [Page {source.metadata.page}] {source.text[:100]}...\n\n"
        avg_score = np.mean([s.score for s in sources])
    else:
        answer = "No relevant information found in the knowledge base."
        avg_score = 0.0

    return ChatResponse(
        answer=answer,
        sources=sources,
        chunk_count=len(sources),
        avg_score=float(avg_score) if sources else 0.0
    )


@app.get("/api/test")
async def test_endpoint():
    """Quick test endpoint with sample queries."""
    global rag

    if rag is None:
        return {"error": "RAG not ready"}

    test_queries = [
        "What is the HireReady program?",
        "What are the eligibility criteria?",
    ]

    results = {}
    for query in test_queries:
        chunks = rag.retrieve(query, top_k=3)
        results[query] = {
            "chunk_count": len(chunks),
            "chunks": [
                {
                    "page": c["metadata"]["page"],
                    "score": c["score"],
                    "text": c["text"][:100]
                }
                for c in chunks
            ]
        }

    return results


@app.get("/api/info")
async def info():
    """Get RAG pipeline info."""
    global rag

    if rag is None:
        return {"error": "RAG not ready"}

    return {
        "embedding_model": "sentence-transformers/multilingual-MiniLM-L12-v2",
        "vector_db": "Faiss (IndexFlatL2)",
        "total_chunks": len(rag.chunks) if rag.chunks else 0,
        "embedding_dimension": rag.index.d if rag.index else 0,
        "retrieval_top_k": 3,
        "min_similarity_score": 0.50
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    import numpy as np
    from typing import Optional

    print("\n" + "="*80)
    print("🚀 STARTING FAISS RAG TEST SERVER")
    print("="*80)
    print("\n📍 Access Points:")
    print("   - API Docs: http://localhost:8001/docs")
    print("   - API ReDoc: http://localhost:8001/redoc")
    print("   - Health: http://localhost:8001/health")
    print("   - Chat: POST http://localhost:8001/api/chat")
    print("   - Test: http://localhost:8001/api/test")
    print("   - Info: http://localhost:8001/api/info")
    print("\n" + "="*80 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
