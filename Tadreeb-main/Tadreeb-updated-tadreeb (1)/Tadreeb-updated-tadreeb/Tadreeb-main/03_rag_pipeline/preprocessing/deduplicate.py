"""
Preprocessing step 2: drop exact-duplicate pages (repeated headers/footers/cover
pages that show up more than once across a document).
Reads and overwrites 02_data/03_processed/<org>_clean.jsonl in place.
"""
import hashlib
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_FOLDER = PROJECT_ROOT / "02_data" / "03_processed"


def deduplicate_pages(pages: list[dict]) -> list[dict]:
    """Keep only the first occurrence of each exact page text."""
    seen_texts = set()
    unique_pages = []
    for page in pages:
        # Compare normalized text: identical PDF covers/boilerplate can have
        # harmless whitespace differences but should not occupy the index twice.
        fingerprint = hashlib.sha256(
            re.sub(r"\s+", " ", page["text"]).strip().lower().encode("utf-8")
        ).hexdigest()
        if fingerprint not in seen_texts:
            seen_texts.add(fingerprint)
            unique_pages.append(page)
    return unique_pages


if __name__ == "__main__":
    for clean_file in sorted(PROCESSED_FOLDER.glob("*_clean.jsonl")):
        pages = [json.loads(line) for line in open(clean_file, "r", encoding="utf-8")]
        unique_pages = deduplicate_pages(pages)

        with open(clean_file, "w", encoding="utf-8") as f:
            for page in unique_pages:
                f.write(json.dumps(page, ensure_ascii=False) + "\n")
        print(f"{clean_file.name}: {len(pages)} -> {len(unique_pages)} pages after dedup")
