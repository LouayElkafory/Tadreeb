"""
Shared ChromaDB config: one persistent local collection for all chunks.
"""
import os
from pathlib import Path
import chromadb

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VECTOR_DB_PATH = str(PROJECT_ROOT / os.getenv("VECTOR_DB_PATH", "./vector_db").lstrip("./"))
COLLECTION_NAME = "tadreeb_chunks"


def get_collection():
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    return client.get_or_create_collection(COLLECTION_NAME)
