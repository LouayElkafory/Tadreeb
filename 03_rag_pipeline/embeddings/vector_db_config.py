"""
Shared ChromaDB config: one persistent local collection for all chunks.
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


def get_collection():
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    return client.get_or_create_collection(COLLECTION_NAME)


def reset_collection():
    """Drop and recreate the collection (needed when the embedding model/dimension changes)."""
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    return client.create_collection(COLLECTION_NAME)

