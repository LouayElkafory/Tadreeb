"""
Shared ChromaDB config: one persistent local collection for all chunks.

The collection is created with cosine distance on purpose. Chroma's default
space is `l2` (SQUARED euclidean), and with L2-normalized embeddings that gives
`d_l2 = 2 - 2*cos`, i.e. a 0..4 range - so any relevance threshold written for
cosine distance (0..2) silently rejects most real matches. Every distance the
retriever sees must therefore come from a cosine collection; `collection_space()`
lets callers assert that instead of guessing.

VECTOR_DB_PATH must point at storage that actually persists across restarts/
deploys. Many hosting platforms (serverless functions, ephemeral containers)
wipe the local filesystem on every deploy or cold start - on those, either
mount a persistent disk/volume and point VECTOR_DB_PATH at it, or re-run
embed_and_store.py as part of the deploy step (see AUTO_INDEX in 06_app/api.py
for an opt-in, non-default alternative).
"""
import os
from pathlib import Path
import chromadb

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_env_path = os.getenv("VECTOR_DB_PATH", "./vector_db")
_vector_path = Path(_env_path)
if not _vector_path.is_absolute():
    _vector_path = PROJECT_ROOT / _vector_path
VECTOR_DB_PATH = str(_vector_path.resolve())
COLLECTION_NAME = "tadreeb_chunks"

# Cosine distance, so retriever thresholds are on a predictable 0..2 scale.
SPACE = "cosine"
_CONFIG = {"hnsw": {"space": SPACE}}


def _client():
    Path(VECTOR_DB_PATH).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=VECTOR_DB_PATH)


def collection_space(collection) -> str:
    """Report the distance space a collection was actually built with."""
    try:
        config = collection.configuration_json or {}
        return (config.get("hnsw") or {}).get("space") or "unknown"
    except Exception:
        return "unknown"


def get_collection():
    collection = _client().get_or_create_collection(COLLECTION_NAME, configuration=_CONFIG)
    space = collection_space(collection)
    if space not in (SPACE, "unknown"):
        # An older index built with the default l2 space: distances are on a
        # different scale, so relevance filtering would be meaningless. Say so
        # loudly rather than quietly returning bad results.
        print(
            f"WARNING: collection '{COLLECTION_NAME}' uses '{space}' distance, not '{SPACE}'. "
            "Re-run 03_rag_pipeline/embeddings/embed_and_store.py to rebuild it.",
            flush=True,
        )
    return collection


def reset_collection():
    """Drop and recreate the collection (needed when the embedding model/dimension/space changes)."""
    client = _client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    return client.create_collection(COLLECTION_NAME, configuration=_CONFIG)
