"""
Stage 1 (data collection): extract raw per-page text from the official PDFs
in 02_data/01_raw/<org>/official/, before any cleaning happens.

Extraction uses PyMuPDF rather than pdfplumber because of the Arabic sources.
pdfplumber returns glyphs in the order they are painted, so a right-to-left
page comes back visually reversed ("دمتعم بردم فلاآ" for "آلاف مدرب معتمد").
That text is unreadable to the embedding model and to the LLM, so those pages
retrieved nothing useful and pushed the model into inventing answers. PyMuPDF
applies bidi reordering and returns proper logical order. pdfplumber stays as a
fallback for any page PyMuPDF yields no text for.
"""
import json
from pathlib import Path

import pymupdf

from text_order import is_visually_ordered

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_FOLDER = PROJECT_ROOT / "02_data" / "01_raw"


def _extract_with_pdfplumber(pdf_path: str, page_number: int) -> str:
    """Fallback for pages PyMuPDF returns nothing for (e.g. odd font encodings)."""
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            return pdf.pages[page_number - 1].extract_text() or ""
    except Exception:
        return ""


def extract_pdf(pdf_path: str) -> list[dict]:
    """Return a list of {"page": int, "text": str} for one PDF, in logical reading order."""
    pages = []
    with pymupdf.open(pdf_path) as doc:
        for index, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            if not text.strip():
                text = _extract_with_pdfplumber(pdf_path, index)
            if is_visually_ordered(text):
                print(f"  WARNING: {Path(pdf_path).name} p{index} still looks right-to-left reversed.")
            pages.append({"page": index, "text": text})
    return pages


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
