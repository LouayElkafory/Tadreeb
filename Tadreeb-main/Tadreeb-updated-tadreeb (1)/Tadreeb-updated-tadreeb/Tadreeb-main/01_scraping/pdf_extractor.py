"""
Stage 1 (data collection): extract raw per-page text from the official PDFs
in 02_data/01_raw/<org>/official/, before any cleaning happens.
"""
import hashlib
import json
from pathlib import Path
import pdfplumber

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_FOLDER = PROJECT_ROOT / "02_data" / "01_raw"


def extract_pdf(pdf_path: Path) -> list[dict]:
    """Return per-page text and extraction metadata for one official PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        return [
            {
                "page": i,
                "text": page.extract_text(layout=True) or "",
            }
            for i, page in enumerate(pdf.pages, start=1)
        ]


def extract_org_pdfs(org_folder: Path) -> list[dict]:
    """Extract every PDF under <org>/official/ and tag pages with document + org."""
    org = org_folder.name
    pages = []
    for pdf_file in sorted((org_folder / "official").glob("*.pdf")):
        document_id = hashlib.sha256(pdf_file.read_bytes()).hexdigest()[:16]
        for page in extract_pdf(pdf_file):
            pages.append(
                {
                    "org": org,
                    "document": pdf_file.name,
                    "document_id": document_id,
                    "source_type": "official_pdf",
                    **page,
                }
            )
    return pages


if __name__ == "__main__":
    for org_folder in sorted(RAW_FOLDER.iterdir()):
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
