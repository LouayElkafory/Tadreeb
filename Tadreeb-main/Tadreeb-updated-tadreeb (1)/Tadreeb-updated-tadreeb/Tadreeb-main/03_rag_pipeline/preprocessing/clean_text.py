"""
Preprocessing step 1: clean raw extracted PDF text.
Reads 02_data/01_raw/<org>/official/<org>_raw.jsonl -> writes 02_data/03_processed/<org>_clean.jsonl
"""
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_FOLDER = PROJECT_ROOT / "02_data" / "01_raw"
PROCESSED_FOLDER = PROJECT_ROOT / "02_data" / "03_processed"


def clean_text(text: str) -> str:
    """Remove extra whitespace and stray characters from extracted PDF text."""
    text = text.replace("\x00", " ").replace("(cid:127)", "•")
    # PDF extractors sometimes leave a space between every Arabic/English
    # character in headings.  Keep normal word spacing intact, but collapse
    # visually empty lines and repeated spaces so embeddings see readable text.
    text = re.sub(r"[\u200b\ufeff]", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def clean_pages(pages: list[dict]) -> list[dict]:
    cleaned = []
    for page in pages:
        text = clean_text(page["text"])
        # A page number or a cover fragment is not useful standalone context.
        if len(text) >= 40:
            cleaned.append({**page, "text": text})
    return cleaned


if __name__ == "__main__":
    PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)
    for raw_file in sorted(RAW_FOLDER.glob("*/official/*_raw.jsonl")):
        org = raw_file.parents[1].name
        pages = [json.loads(line) for line in open(raw_file, "r", encoding="utf-8")]
        cleaned = clean_pages(pages)

        output_path = PROCESSED_FOLDER / f"{org}_clean.jsonl"
        with open(output_path, "w", encoding="utf-8") as f:
            for page in cleaned:
                f.write(json.dumps(page, ensure_ascii=False) + "\n")
        print(f"Cleaned {len(cleaned)} pages -> {output_path}")
