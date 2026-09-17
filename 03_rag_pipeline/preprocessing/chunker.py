"""
Preprocessing step 3: split cleaned page text into overlapping, sentence-aware chunks.
Reads 02_data/03_processed/<org>_clean.jsonl -> writes 02_data/04_chunks/<org>_chunks.jsonl
"""
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_FOLDER = PROJECT_ROOT / "02_data" / "03_processed"
CHUNKS_FOLDER = PROJECT_ROOT / "02_data" / "04_chunks"


CHUNK_SIZE = 500
OVERLAP = 100
MIN_CHUNK_SIZE = 40  # drop trailing scraps too short to carry standalone meaning

# Arabic and Latin sentence terminators, plus newlines as a weaker boundary.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?؟۔])\s+|\n+")


def split_sentences(text: str) -> list[str]:
    """Split text into sentence-ish units without cutting words apart."""
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
    return sentences


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """
    Pack sentences into chunks of up to chunk_size characters, never splitting a
    sentence/word in half. Consecutive chunks overlap by roughly `overlap` characters
    of trailing sentences so context isn't lost at chunk boundaries.
    """
    sentences = split_sentences(text)
    if not sentences:
        return []

    # A single sentence longer than chunk_size still needs a hard split (rare, e.g. lists
    # or tables with no punctuation) — fall back to word-boundary splitting for it.
    def hard_split(sentence: str) -> list[str]:
        words = sentence.split(" ")
        pieces, current = [], ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) > chunk_size and current:
                pieces.append(current)
                current = word
            else:
                current = candidate
        if current:
            pieces.append(current)
        return pieces

    units = []
    for sentence in sentences:
        if len(sentence) > chunk_size:
            units.extend(hard_split(sentence))
        else:
            units.append(sentence)

    chunks = []
    current_units: list[str] = []
    current_len = 0

    def flush():
        if current_units:
            chunks.append(" ".join(current_units).strip())

    for unit in units:
        if current_len + len(unit) + 1 > chunk_size and current_units:
            flush()
            # carry trailing sentences into the next chunk for overlap continuity
            carry, carry_len = [], 0
            for u in reversed(current_units):
                if carry_len + len(u) > overlap:
                    break
                carry.insert(0, u)
                carry_len += len(u) + 1
            current_units = carry
            current_len = carry_len

        current_units.append(unit)
        current_len += len(unit) + 1

    flush()

    return [c for c in chunks if len(c) >= MIN_CHUNK_SIZE]


def chunk_pages(pages: list[dict]) -> list[dict]:
    """Turn cleaned pages into chunks, each keeping org/document/page metadata."""
    all_chunks = []
    for page in pages:
        for piece in chunk_text(page["text"]):
            all_chunks.append({
                "org": page["org"],
                "document": page["document"],
                "page": page["page"],
                "text": piece,
            })
    return all_chunks


if __name__ == "__main__":
    Path(CHUNKS_FOLDER).mkdir(parents=True, exist_ok=True)
    for clean_file in sorted(Path(PROCESSED_FOLDER).glob("*_clean.jsonl")):
        org = clean_file.stem.replace("_clean", "")
        pages = [json.loads(line) for line in open(clean_file, "r", encoding="utf-8")]
        chunks = chunk_pages(pages)

        output_path = Path(CHUNKS_FOLDER) / f"{org}_chunks.jsonl"
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
        print(f"Chunked {len(pages)} pages -> {len(chunks)} chunks -> {output_path}")
