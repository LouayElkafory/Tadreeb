"""
Embed every chunk (sentence-transformers model) and store it in the local ChromaDB collection.
Reads 02_data/04_chunks/*_chunks.jsonl -> writes into the persistent vector DB.

Each chunk is embedded together with its source line ("DEPI / Technical Tracks
Catalog"), not on its own. A lot of the catalogue chunks are bare fragments -
"1. Huawei Network Administrator 31 2. Fortinet Cybersecurity Engineer 32" -
with nothing in the text saying which programme they belong to, so a question
naming the organisation had no way to reach them. The raw text is what gets
stored and shown to the model; only the vector is built from the prefixed form.
"""
import json
import sys
from pathlib import Path

from embedding_utils import EMBEDDING_MODEL, embed_texts
from vector_db_config import reset_collection

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "03_rag_pipeline" / "preprocessing"))
from structure import document_profiles, enrich  # noqa: E402

CHUNKS_FOLDER = PROJECT_ROOT / "02_data" / "04_chunks"
BATCH_SIZE = 64

# The structured fields come from 03_rag_pipeline/preprocessing/structure.py and
# are what retrieval filters and boosts on: a question about the duration of a
# named track is answered by prioritising `org` + `category=duration` + `track`.
# They are listed here so a full rebuild reproduces them instead of dropping them.
METADATA_FIELDS = (
    "org", "document", "page", "title", "url", "source_type",
    "category", "categories", "program", "track", "specialization",
    "duration", "duration_unit", "training_type",
)


def contextualize(chunk: dict) -> str:
    """The text actually fed to the embedding model: source header + chunk body."""
    parts = [
        str(chunk.get("org", "")).upper(),
        str(chunk.get("title") or chunk.get("document") or ""),
        chunk.get("text", ""),
    ]
    return "\n".join(part for part in parts if part)


def chunk_metadata(chunk: dict) -> dict:
    """Chroma only accepts scalar metadata values, and rejects None.

    Listing the fields explicitly also drops the non-scalar ones `enrich()`
    returns for the knowledge-base builder (`specializations` is a list).
    """
    return {
        key: chunk[key]
        for key in METADATA_FIELDS
        if isinstance(chunk.get(key), (str, int, float, bool)) and chunk.get(key) != ""
    }


def structure_chunks(chunks: list[dict]) -> list[dict]:
    """Attach the structured metadata (category, track, duration, ...) to each chunk."""
    profiles = document_profiles(chunks)
    return [
        {**chunk, **enrich(chunk, profiles.get((chunk.get("org", ""), chunk.get("document", ""))))}
        for chunk in chunks
    ]


def main() -> int:
    print(f"Using embedding model: {EMBEDDING_MODEL}", flush=True)
    chunk_files = sorted(Path(CHUNKS_FOLDER).glob("*_chunks.jsonl"))
    if not chunk_files:
        print(f"No chunk files in {CHUNKS_FOLDER}. Run the preprocessing steps first.", flush=True)
        return 1

    collection = reset_collection()  # rebuild fresh so stale/old-space vectors never linger

    for chunk_file in chunk_files:
        with open(chunk_file, "r", encoding="utf-8") as f:
            chunks = [json.loads(line) for line in f if line.strip()]
        if not chunks:
            continue
        chunks = structure_chunks(chunks)
        print(f"Embedding {len(chunks)} chunks from {chunk_file.name}...", flush=True)

        ids = [f"{chunk_file.stem}-{i}" for i in range(len(chunks))]
        documents = [c["text"] for c in chunks]
        metadatas = [chunk_metadata(c) for c in chunks]
        to_embed = [contextualize(c) for c in chunks]

        embeddings = []
        for start in range(0, len(to_embed), BATCH_SIZE):
            embeddings.extend(embed_texts(to_embed[start:start + BATCH_SIZE]))
            done = min(start + BATCH_SIZE, len(to_embed))
            print(f"  Processed {done}/{len(to_embed)} chunks", flush=True)

        collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        print(f"Stored {len(chunks)} chunks from {chunk_file.name}\n", flush=True)

    print(f"Done. Collection now has {collection.count()} chunks.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
