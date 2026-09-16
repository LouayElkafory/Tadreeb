"""
Embed every chunk (Ollama embedding model) and store it in the local ChromaDB collection.
Reads 02_data/04_chunks/*.jsonl -> writes into the persistent vector DB.
"""
import argparse
import hashlib
import json
from pathlib import Path
import ollama

from vector_db_config import (
    get_collection,
    EMBEDDING_MODEL,
    VECTOR_DB_PATH,
    COLLECTION_NAME,
    COLLECTION_METADATA,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_FOLDER = PROJECT_ROOT / "02_data" / "04_chunks"
BATCH_SIZE = 48


def embed_text(text: str) -> list[float]:
    return ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)["embedding"]


def verify_collection(collection, expected_count: int) -> None:
    """Never assume storage worked - print a quick, honest sanity check."""
    count = collection.count()
    print("\n--- Vector DB verification ---")
    print(f"Vector DB path: {VECTOR_DB_PATH}")
    print(f"Collection name: {COLLECTION_NAME}")
    print(f"Number of stored chunks: {count}")

    if count != expected_count:
        raise RuntimeError(f"Expected {expected_count} chunks in Chroma, found {count}.")
    if count:
        sample = collection.peek(limit=1)
        print(f"Sample chunk text: {sample['documents'][0][:120]}...")
        print(f"Sample metadata: {sample['metadatas'][0]}")
    else:
        print("WARNING: collection is empty - nothing was stored.")


def stable_id(chunk: dict) -> str:
    """A repeatable ID changes whenever the document/page/text changes."""
    payload = "|".join(
        str(chunk.get(key, "")) for key in ("org", "document_id", "document", "page", "chunk_index", "text")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def rebuild_collection() -> object:
    """Replace the collection so deleted/stale chunks cannot survive a rebuild."""
    import chromadb

    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Removed previous collection: {COLLECTION_NAME}")
    except Exception:
        pass  # first build: there is no collection yet
    return client.get_or_create_collection(COLLECTION_NAME, metadata=COLLECTION_METADATA)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed official RAG chunks into ChromaDB.")
    parser.add_argument("--append", action="store_true", help="Upsert without clearing the existing collection.")
    args = parser.parse_args()
    collection = get_collection() if args.append else rebuild_collection()
    expected_count = 0

    for chunk_file in sorted(CHUNKS_FOLDER.glob("*_chunks.jsonl")):
        chunks = [json.loads(line) for line in open(chunk_file, "r", encoding="utf-8")]
        expected_count += len(chunks)
        for start in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[start : start + BATCH_SIZE]
            collection.upsert(
                ids=[stable_id(c) for c in batch],
                embeddings=[embed_text(c["text"]) for c in batch],
                documents=[c["text"] for c in batch],
                metadatas=[
                    {
                        "org": c["org"], "document": c["document"], "document_id": c.get("document_id", ""),
                        "page": c["page"], "chunk_index": c["chunk_index"],
                    }
                    for c in batch
                ],
            )
        print(f"Stored {len(chunks)} chunks from {chunk_file.name}")

    verify_collection(collection, expected_count)
