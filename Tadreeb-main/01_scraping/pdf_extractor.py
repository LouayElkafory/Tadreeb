"""
Stage 1 (data collection): extract raw per-page text from the official PDFs
in 02_data/01_raw/<org>/official/, before any cleaning happens.
"""
import json
from pathlib import Path
import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_FOLDER = PROJECT_ROOT / "02_data" / "01_raw"


def extract_pdf(pdf_path: str) -> list[dict]:
    """Return a list of {"page": int, "text": str} for one PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        return [{"page": i, "text": page.extract_text() or ""} for i, page in enumerate(pdf.pages, start=1)]


def extract_org_pdfs(org_folder: Path) -> list[dict]:
    """Extract every PDF under <org>/official/ and tag pages with document + org."""
    org = org_folder.name
    pages = []
    for pdf_file in sorted((org_folder / "official").glob("*.pdf")):
        for page in extract_pdf(str(pdf_file)):
            pages.append({"org": org, "document": pdf_file.name, **page})
    return pages


if __name__ == "__main__":
    for org_folder in sorted(Path(RAW_FOLDER).iterdir()):
        if not org_folder.is_dir():
            continue
        pages = extract_org_pdfs(org_folder)
        if not pages:
            continue
        output_path = org_folder / "official" / f"{org_folder.name}_raw.jsonl"
        with open(output_path, "w", encoding="utf-8") as f:
            for page in pages:
                f.write(json.dumps(page, ensure_ascii=False) + "\n")
        print(f"Extracted {len(pages)} pages -> {output_path}")
