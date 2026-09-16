"""
Embed every chunk (Ollama embedding model) and store it in the local ChromaDB collection.
Reads 02_data/04_chunks/*.jsonl -> writes into the persistent vector DB.
"""
import json
from pathlib import Path
import ollama

from vector_db_config import get_collection, EMBEDDING_MODEL, VECTOR_DB_PATH, COLLECTION_NAME

CHUNKS_FOLDER = "../../02_data/04_chunks"


def embed_text(text: str) -> list[float]:
    return ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)["embedding"]


def verify_collection(collection) -> None:
    """Never assume storage worked - print a quick, honest sanity check."""
    count = collection.count()
    print("\n--- Vector DB verification ---")
    print(f"Vector DB path: {VECTOR_DB_PATH}")
    print(f"Collection name: {COLLECTION_NAME}")
    print(f"Number of stored chunks: {count}")

    if count:
        sample = collection.peek(limit=1)
        print(f"Sample chunk text: {sample['documents'][0][:120]}...")
        print(f"Sample metadata: {sample['metadatas'][0]}")
    else:
        print("WARNING: collection is empty - nothing was stored.")


if __name__ == "__main__":
    collection = get_collection()

    for chunk_file in sorted(Path(CHUNKS_FOLDER).glob("*_chunks.jsonl")):
        chunks = [json.loads(line) for line in open(chunk_file, "r", encoding="utf-8")]

        ids = [f"{c['org']}-{c['document']}-p{c['page']}-{i}" for i, c in enumerate(chunks)]
        embeddings = [embed_text(c["text"]) for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [{"org": c["org"], "document": c["document"], "page": c["page"]} for c in chunks]

        collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        print(f"Stored {len(chunks)} chunks from {chunk_file.name}")

    verify_collection(collection)
