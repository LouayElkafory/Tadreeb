"""
Shared sentence-transformers embedding model loader.
Used by both embed_and_store.py (indexing) and retriever.py (query time)
so the exact same model/weights are used on both sides of the vector search.
"""
import os
from functools import lru_cache

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")


@lru_cache(maxsize=1)
def get_embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL)


def embed_text(text: str) -> list[float]:
    return get_embedder().encode(text, normalize_embeddings=True).tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    return get_embedder().encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()
