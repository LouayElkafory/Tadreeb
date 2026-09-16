"""
Shared ChromaDB config: one persistent local collection for all chunks.
Single source of truth for VECTOR_DB_PATH / COLLECTION_NAME / EMBEDDING_MODEL -
both embed_and_store.py (storage) and retriever.py (query) import these from
here so they can never drift apart.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
import chromadb

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VECTOR_DB_PATH = str(PROJECT_ROOT / os.getenv("VECTOR_DB_PATH", "./vector_db").lstrip("./"))
COLLECTION_NAME = "tadreeb_chunks"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")


def get_collection():
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    return client.get_or_create_collection(COLLECTION_NAME)
