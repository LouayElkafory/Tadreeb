"""
Adds the structured metadata to a vector DB that was built before it existed, and
indexes the knowledge-base fact cards - without rebuilding anything.

    python 03_rag_pipeline/embeddings/backfill_structure.py

Two passes, both additive:

1. **Existing chunks** get their `category`, `track`, `program`, `duration` and
   `training_type` written with `collection.update()`, which changes metadata
   only. The text and the embedding vectors are not touched, so nothing has to be
   re-embedded and no existing answer changes except in how it ranks.

2. **Fact cards** from `02_data/04_chunks/*_structured_chunks.jsonl` are embedded
   and `upsert`ed with deterministic ids, exactly as `collect_web_data.py` does -
   so re-running updates them in place instead of duplicating them.

Use this instead of `embed_and_store.py` when you want to keep the vectors you
already have. `embed_and_store.py` produces the same metadata from scratch, but
it resets the collection and re-embeds all ~1,700 chunks to do it.

Safe to re-run: pass 1 recomputes the same values, and pass 2 upserts the same
ids. Nothing is ever deleted.
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(PROJECT_ROOT / "03_rag_pipeline" / "preprocessing"))

from embed_and_store import chunk_metadata, contextualize  # noqa: E402
from embedding_utils import EMBEDDING_MODEL, embed_texts  # noqa: E402
from structure import document_profiles, enrich  # noqa: E402
from vector_db_config import get_collection  # noqa: E402

CHUNKS_FOLDER = PROJECT_ROOT / "02_data" / "04_chunks"
BATCH_SIZE = 64
UPDATE_BATCH = 400


def backfill_existing(collection) -> int:
    """Write structured metadata onto every chunk already in the collection."""
    stored = collection.get(include=["documents", "metadatas"])
    if not stored["ids"]:
        print("Collection is empty - run embed_and_store.py first.")
        return 0

    chunks = [
        {**(metadata or {}), "text": text}
        for text, metadata in zip(stored["documents"], stored["metadatas"])
    ]
    profiles = document_profiles(chunks)

    ids, metadatas, changed = [], [], 0
    for chunk_id, chunk in zip(stored["ids"], chunks):
        key = (chunk.get("org", ""), chunk.get("document", ""))
        enriched = {**chunk, **enrich(chunk, profiles.get(key))}
        metadata = chunk_metadata(enriched)
        # Only send the rows that actually change, so a re-run is nearly free.
        current = {k: v for k, v in chunk.items() if k != "text"}
        if metadata != current:
            ids.append(chunk_id)
            metadatas.append(metadata)
            changed += 1

    for start in range(0, len(ids), UPDATE_BATCH):
        collection.update(
            ids=ids[start:start + UPDATE_BATCH],
            metadatas=metadatas[start:start + UPDATE_BATCH],
        )
    print(f"Pass 1: updated metadata on {changed} of {len(stored['ids'])} existing chunks "
          f"(text and vectors untouched).")
    return changed


def index_fact_cards(collection) -> int:
    """Embed and upsert the knowledge-base fact cards."""
    card_files = sorted(CHUNKS_FOLDER.glob("*_structured_chunks.jsonl"))
    if not card_files:
        print("Pass 2: no fact cards found - run preprocessing/build_knowledge_base.py first.")
        return 0

    total = 0
    for path in card_files:
        with open(path, "r", encoding="utf-8") as f:
            cards = [json.loads(line) for line in f if line.strip()]
        if not cards:
            continue

        ids = [f"{path.stem}-{i}" for i in range(len(cards))]
        documents = [c["text"] for c in cards]
        metadatas = [chunk_metadata(c) for c in cards]
        to_embed = [contextualize(c) for c in cards]

        embeddings: list[list[float]] = []
        for start in range(0, len(to_embed), BATCH_SIZE):
            embeddings.extend(embed_texts(to_embed[start:start + BATCH_SIZE]))

        collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        total += len(cards)
        print(f"Pass 2: indexed {len(cards):3d} fact cards from {path.name}")
    return total


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    print(f"Embedding model: {EMBEDDING_MODEL}")
    collection = get_collection()
    before = collection.count()
    print(f"Collection holds {before} chunks.\n")

    backfill_existing(collection)
    cards = index_fact_cards(collection)

    after = collection.count()
    print(f"\nDone. {before} -> {after} chunks ({cards} fact cards indexed; "
          f"no existing chunk was deleted or re-embedded).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
