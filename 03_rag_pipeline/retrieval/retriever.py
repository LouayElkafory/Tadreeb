"""
Retrieval: embed the user's question and find the most relevant chunks in ChromaDB.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "embeddings"))
from embedding_utils import embed_text
from vector_db_config import get_collection

TOP_K = 3
CANDIDATE_POOL = 8  # over-fetch, then keep only chunks that clear the relevance floor
MAX_DISTANCE = 0.9  # cosine distance floor (embeddings are normalized); drops off-topic chunks


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    """Return the top_k most relevant chunks for a question, with their metadata."""
    collection = get_collection()
    question_embedding = embed_text(question)

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=min(CANDIDATE_POOL, max(top_k, collection.count())),
    )

    if not results["documents"] or not results["documents"][0]:
        return []

    chunks = []
    for text, metadata, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        if distance <= MAX_DISTANCE:
            chunks.append({**metadata, "text": text, "distance": distance})

    return chunks[:top_k]
