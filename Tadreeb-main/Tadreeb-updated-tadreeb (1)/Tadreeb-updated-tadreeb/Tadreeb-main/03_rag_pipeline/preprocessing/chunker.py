"""
Preprocessing step 3: split cleaned page text into overlapping chunks.
Reads 02_data/03_processed/<org>_clean.jsonl -> writes 02_data/04_chunks/<org>_chunks.jsonl
"""
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_FOLDER = PROJECT_ROOT / "02_data" / "03_processed"
CHUNKS_FOLDER = PROJECT_ROOT / "02_data" / "04_chunks"

# Character-based limits deliberately keep chunks compact enough for precise
# retrieval while preserving complete sentences and table rows.
CHUNK_SIZE = 900
OVERLAP = 150
MIN_CHUNK_SIZE = 100


def _units(text: str) -> list[str]:
    """Split on paragraphs/sentences without breaking Arabic or English words."""
    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    units: list[str] = []
    for paragraph in paragraphs:
        # Keep bullet/table rows whole where possible; split long prose at a
        # sentence boundary.  Arabic and English punctuation are both covered.
        parts = re.split(r"(?<=[.!?؟؛])\s+", paragraph)
        units.extend(part.strip() for part in parts if part.strip())
    return units or [text.strip()]


def _split_long_unit(unit: str, chunk_size: int) -> list[str]:
    """Fallback for a very long table row: prefer whitespace before a hard cut."""
    pieces = []
    remaining = unit
    while len(remaining) > chunk_size:
        cut = remaining.rfind(" ", 0, chunk_size + 1)
        cut = cut if cut >= chunk_size // 2 else chunk_size
        pieces.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        pieces.append(remaining)
    return pieces


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """Create sentence-aware, overlapping chunks and discard unusable fragments."""
    chunks: list[str] = []
    current = ""
    for unit in _units(text):
        for part in _split_long_unit(unit, chunk_size):
            candidate = f"{current} {part}".strip() if current else part
            if current and len(candidate) > chunk_size:
                if len(current) >= MIN_CHUNK_SIZE:
                    chunks.append(current)
                overlap_text = current[-overlap:].split(" ", 1)
                overlap_text = overlap_text[-1] if len(overlap_text) == 2 else current[-overlap:]
                current = f"{overlap_text} {part}".strip()
            else:
                current = candidate
    if len(current) >= MIN_CHUNK_SIZE:
        chunks.append(current)
    return chunks


def chunk_pages(pages: list[dict]) -> list[dict]:
    """Turn cleaned pages into chunks, each keeping org/document/page metadata."""
    all_chunks = []
    for page in pages:
        for index, piece in enumerate(chunk_text(page["text"])):
            all_chunks.append({
                "org": page["org"],
                "document": page["document"],
                "document_id": page.get("document_id", ""),
                "page": page["page"],
                "chunk_index": index,
                "text": piece,
            })
    return all_chunks


if __name__ == "__main__":
    CHUNKS_FOLDER.mkdir(parents=True, exist_ok=True)
    for clean_file in sorted(PROCESSED_FOLDER.glob("*_clean.jsonl")):
        org = clean_file.stem.replace("_clean", "")
        pages = [json.loads(line) for line in open(clean_file, "r", encoding="utf-8")]
        chunks = chunk_pages(pages)

        output_path = CHUNKS_FOLDER / f"{org}_chunks.jsonl"
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
        print(f"Chunked {len(pages)} pages -> {len(chunks)} chunks -> {output_path}")
