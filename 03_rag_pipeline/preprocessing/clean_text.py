"""
Preprocessing step 1: clean raw extracted PDF text.
Reads 02_data/01_raw/<org>/official/<org>_raw.jsonl -> writes 02_data/03_processed/<org>_clean.jsonl
"""
import json
import re
from pathlib import Path

RAW_FOLDER = "../../02_data/01_raw"
PROCESSED_FOLDER = "../../02_data/03_processed"


def clean_text(text: str) -> str:
    """Remove extra whitespace and stray characters from extracted PDF text."""
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def clean_pages(pages: list[dict]) -> list[dict]:
    cleaned = []
    for page in pages:
        text = clean_text(page["text"])
        if text:
            cleaned.append({**page, "text": text})
    return cleaned


if __name__ == "__main__":
    Path(PROCESSED_FOLDER).mkdir(parents=True, exist_ok=True)
    for raw_file in sorted(Path(RAW_FOLDER).glob("*/official/*_raw.jsonl")):
        org = raw_file.parents[1].name
        pages = [json.loads(line) for line in open(raw_file, "r", encoding="utf-8")]
        cleaned = clean_pages(pages)

        output_path = Path(PROCESSED_FOLDER) / f"{org}_clean.jsonl"
        with open(output_path, "w", encoding="utf-8") as f:
            for page in cleaned:
                f.write(json.dumps(page, ensure_ascii=False) + "\n")
        print(f"Cleaned {len(cleaned)} pages -> {output_path}")
