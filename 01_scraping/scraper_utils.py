"""
Helper utilities for web scrapers (session, HTML parsing, text extraction, JSONL output).
"""
import json
import logging
import re
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ar,en-US;q=0.7,en;q=0.3",
}


def fetch_url(url: str, timeout: int = 15, max_retries: int = 2) -> str | None:
    """Fetch HTML content from a URL with retries."""
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout)
            if response.status_code == 200:
                response.encoding = response.apparent_encoding or "utf-8"
                return response.text
            logger.warning(f"HTTP {response.status_code} for {url}")
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(1)
    return None


def extract_clean_text(html: str) -> str:
    """Extract clean readable text from HTML markup, discarding nav/scripts/styles."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    # Clean redundant whitespace and empty lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned_text = "\n".join(lines)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    return cleaned_text


def save_pages_jsonl(pages: list[dict], output_path: Path):
    """Save a list of page dicts to a jsonl file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for p in pages:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    logger.info(f"Saved {len(pages)} scraped pages to {output_path}")
