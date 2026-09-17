"""
Embed every chunk (sentence-transformers model) and store it in the local ChromaDB collection.
Reads 02_data/04_chunks/*.jsonl -> writes into the persistent vector DB.
"""
import json
from pathlib import Path

from embedding_utils import EMBEDDING_MODEL, embed_texts
from vector_db_config import reset_collection

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_FOLDER = PROJECT_ROOT / "02_data" / "04_chunks"
BATCH_SIZE = 64


if __name__ == "__main__":
    print(f"Using embedding model: {EMBEDDING_MODEL}", flush=True)
    collection = reset_collection()  # rebuild fresh so stale/old-dimension vectors never linger

    for chunk_file in sorted(Path(CHUNKS_FOLDER).glob("*_chunks.jsonl")):
        chunks = [json.loads(line) for line in open(chunk_file, "r", encoding="utf-8")]
        print(f"Embedding {len(chunks)} chunks from {chunk_file.name}...", flush=True)

        ids = [f"{c['org']}-{c['document']}-p{c['page']}-{i}" for i, c in enumerate(chunks)]
        documents = [c["text"] for c in chunks]
        metadatas = [{"org": c["org"], "document": c["document"], "page": c["page"]} for c in chunks]

        embeddings = []
        for start in range(0, len(documents), BATCH_SIZE):
            batch = documents[start:start + BATCH_SIZE]
            embeddings.extend(embed_texts(batch))
            done = min(start + BATCH_SIZE, len(documents))
            print(f"  Processed {done}/{len(documents)} chunks", flush=True)

        collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        print(f"Stored {len(chunks)} chunks from {chunk_file.name}\n", flush=True)

    print(f"Done. Collection now has {collection.count()} chunks.", flush=True)
