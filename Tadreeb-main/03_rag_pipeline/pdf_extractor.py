"""
PDF extraction with PyMuPDF (fallback to PyPDF) and text cleaning.
Supports both English and Arabic text normalization.
"""
import re
from pathlib import Path

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from PyPDF2 import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


def clean_text(text: str) -> str:
    """Remove PDF artifacts, null bytes, zero-width chars, normalize whitespace."""
    if not text:
        return ""

    # Remove null bytes and zero-width characters
    text = text.replace('\x00', '')
    text = re.sub(r'[​‌‍﻿]', '', text)

    # Remove PDF markers and control characters
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)

    # Normalize whitespace (preserve single line breaks for paragraphs)
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines → double newline
    text = re.sub(r'[ \t]+', ' ', text)      # Multiple spaces/tabs → single space
    text = re.sub(r' +\n', '\n', text)       # Trailing spaces before newline
    text = re.sub(r'\n +', '\n', text)       # Leading spaces after newline

    return text.strip()


def extract_with_pymupdf(pdf_path: Path) -> list[dict]:
    """Extract text using PyMuPDF (fitz)."""
    if not HAS_PYMUPDF:
        raise ImportError("PyMuPDF not installed")

    pages = []
    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()
            text = clean_text(text)
            pages.append({
                "page": page_num,
                "text": text,
                "extractor": "pymupdf"
            })
    return pages


def extract_with_pypdf(pdf_path: Path) -> list[dict]:
    """Extract text using PyPDF (fallback)."""
    if not HAS_PYPDF:
        raise ImportError("PyPDF not installed")

    pages = []
    reader = PdfReader(pdf_path)
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = clean_text(text)
        pages.append({
            "page": page_num,
            "text": text,
            "extractor": "pypdf"
        })
    return pages


def extract_pdf(pdf_path: Path) -> list[dict]:
    """Extract text from PDF with automatic fallback. Returns per-page text."""
    pdf_path = Path(pdf_path)

    if HAS_PYMUPDF:
        return extract_with_pymupdf(pdf_path)
    elif HAS_PYPDF:
        return extract_with_pypdf(pdf_path)
    else:
        raise ImportError("Neither PyMuPDF nor PyPDF installed. Install: pip install pymupdf pypdf")


def extract_org_pdfs(org_folder: Path) -> list[dict]:
    """Extract all PDFs from <org>/official/ and tag with metadata."""
    import hashlib

    org = org_folder.name
    pages = []
    official_dir = org_folder / "official"

    if not official_dir.exists():
        return pages

    for pdf_file in sorted(official_dir.glob("*.pdf")):
        try:
            document_id = hashlib.sha256(pdf_file.read_bytes()).hexdigest()[:16]
            for page in extract_pdf(pdf_file):
                pages.append({
                    "org": org,
                    "document": pdf_file.name,
                    "document_id": document_id,
                    "source_type": "official_pdf",
                    **page,
                })
        except Exception as e:
            print(f"Warning: Failed to extract {pdf_file}: {e}")
            continue

    return pages
