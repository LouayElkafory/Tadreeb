"""
Retrieval: embed the user's question and find the most relevant chunks in ChromaDB.
"""
import os
import sys
from pathlib import Path
import ollama

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "embeddings"))
from vector_db_config import get_collection

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
TOP_K = 3


def embed_text(text: str) -> list[float]:
    return ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)["embedding"]


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    """Return the top_k most relevant chunks for a question, with their metadata."""
    collection = get_collection()
    question_embedding = embed_text(question)

    results = collection.query(query_embeddings=[question_embedding], n_results=top_k)

    chunks = []
    for text, metadata in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({**metadata, "text": text})
    return chunks
