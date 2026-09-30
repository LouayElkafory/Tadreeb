"""
Preprocessing step 1: clean raw extracted PDF text.
Reads 02_data/01_raw/<org>/official/<org>_raw.jsonl -> writes 02_data/03_processed/<org>_clean.jsonl

Cleaning is deliberately conservative: whitespace tidying plus Unicode
normalisation. Arabic reading order is fixed upstream in the extractor
(01_scraping/pdf_extractor.py) where the PDF's own layout information is still
available; here we only *check* for visually-ordered text and warn, because a
blind reversal at this stage cannot tell the definite article "ال" apart from a
lam-alef ligature and would corrupt otherwise-good pages.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "01_scraping"))
from text_order import is_visually_ordered  # noqa: E402

RAW_FOLDER = PROJECT_ROOT / "02_data" / "01_raw"
PROCESSED_FOLDER = PROJECT_ROOT / "02_data" / "03_processed"

# Arabic diacritics and the tatweel stretch character: invisible to a reader but
# they split a word into different tokens for the embedding model.
_DIACRITICS = re.compile("[\u064B-\u065F\u0670\u0640]")


def clean_text(text: str) -> str:
    """Remove extra whitespace and stray characters from extracted PDF text."""
    text = text.replace("\x00", " ")
    # Presentation forms (ﻻ, ﻲ, ...) fold back to standard letters.
    text = unicodedata.normalize("NFKC", text)
    text = _DIACRITICS.sub("", text)
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
    org_pages: dict[str, list[dict]] = {}
    for raw_file in sorted(Path(RAW_FOLDER).glob("*/official/*_raw.jsonl")):
        org = raw_file.parents[1].name
        pages = [json.loads(line) for line in open(raw_file, "r", encoding="utf-8")]
        broken = [p["page"] for p in pages if is_visually_ordered(p["text"])]
        if broken:
            print(f"  WARNING: {raw_file.name} pages {broken} are right-to-left reversed. "
                  f"Re-run 01_scraping/pdf_extractor.py to re-extract them.")
        org_pages.setdefault(org, []).extend(clean_pages(pages))

    for org, pages in org_pages.items():
        output_path = Path(PROCESSED_FOLDER) / f"{org}_clean.jsonl"
        with open(output_path, "w", encoding="utf-8") as f:
            for page in pages:
                f.write(json.dumps(page, ensure_ascii=False) + "\n")
        print(f"Cleaned {len(pages)} pages for {org} -> {output_path}")
