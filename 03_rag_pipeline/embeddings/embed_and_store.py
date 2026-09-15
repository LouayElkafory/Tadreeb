"""
Embed every chunk (Ollama embedding model) and store it in the local ChromaDB collection.
Reads 02_data/04_chunks/*.jsonl -> writes into the persistent vector DB.
"""
import json
import os
from pathlib import Path
import ollama

from vector_db_config import get_collection

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
CHUNKS_FOLDER = "../../02_data/04_chunks"


def embed_text(text: str) -> list[float]:
    return ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)["embedding"]


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
