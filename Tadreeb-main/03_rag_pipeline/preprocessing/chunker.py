"""
Preprocessing step 3: split cleaned page text into overlapping chunks.
Reads 02_data/03_processed/<org>_clean.jsonl -> writes 02_data/04_chunks/<org>_chunks.jsonl
"""
import json
from pathlib import Path

PROCESSED_FOLDER = "../../02_data/03_processed"
CHUNKS_FOLDER = "../../02_data/04_chunks"

CHUNK_SIZE = 500
OVERLAP = 50


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """Split text into overlapping fixed-size chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


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
