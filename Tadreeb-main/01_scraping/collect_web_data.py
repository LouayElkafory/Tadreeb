"""
Collect general public information about ITI, NTI, DEPI and ITIDA from official
web sources and ADD it to the existing vector DB.

    python collect_web_data.py

Every run processes all four organisations:

    Official Web Sources -> Collect -> Clean -> Chunk -> Embed -> Add New Vectors
                                                                       |
                                                              Existing Vector DB

Nothing existing is touched. The PDFs, the `<org>_clean.jsonl` / `<org>_chunks.jsonl`
files produced by the normal pipeline, and every vector already in ChromaDB stay
exactly as they are:

* raw pages go to a NEW folder, `02_data/01_raw/<org>/web/`, which is outside the
  `*/official/*_raw.jsonl` glob that `clean_text.py` reads, so the existing
  cleaning/chunking stages produce byte-identical output;
* chunks go to NEW files, `02_data/04_chunks/<org>_web_chunks.jsonl`. They match
  the `*_chunks.jsonl` glob that `embed_and_store.py` uses, on purpose: a later
  full rebuild re-indexes the web data too, with the same ids, instead of
  silently losing it;
* vectors are added with `collection.upsert()` on the existing collection. This
  script never calls `reset_collection()` - that is `embed_and_store.py`'s job.

Ids are deterministic (`<org>_web_chunks-<n>`, the same scheme
`embed_and_store.py` uses), so re-running updates a chunk in place rather than
adding a second copy of it. Text that already exists in the collection under a
different id is skipped.

Every stage is reused from the existing pipeline - `clean_text()`, `chunk_pages()`,
`embed_texts()`, `contextualize()` - so web data is cleaned, chunked and embedded
exactly like the PDF data it sits next to.

Dependencies: `requests` and `beautifulsoup4`, both already used by the other
scrapers in this folder. Nothing new is added.
"""
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))                          # scraper_utils, depi_api
sys.path.insert(0, str(PROJECT_ROOT / "03_rag_pipeline" / "preprocessing"))       # clean_text, chunker
sys.path.insert(0, str(PROJECT_ROOT / "03_rag_pipeline" / "embeddings"))          # embeddings + vector DB

from scraper_utils import HEADERS, extract_clean_text  # noqa: E402
from clean_text import clean_text  # noqa: E402
from chunker import chunk_pages  # noqa: E402
from embedding_utils import EMBEDDING_MODEL, embed_texts  # noqa: E402
from embed_and_store import contextualize, chunk_metadata, structure_chunks  # noqa: E402
from vector_db_config import get_collection  # noqa: E402
from depi_api import collect_depi_pages  # noqa: E402

# Windows consoles default to a legacy code page that cannot encode Arabic.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

RAW_FOLDER = PROJECT_ROOT / "02_data" / "01_raw"
CHUNKS_FOLDER = PROJECT_ROOT / "02_data" / "04_chunks"

ORGANIZATIONS = ["ITI", "NTI", "DEPI", "ITIDA"]

REQUEST_DELAY = 1.0      # polite pause between requests to the same site
MAX_PAGES_PER_ORG = 14
MIN_PAGE_TEXT = 200      # below this a page is treated as an empty app shell
MIN_SUMMARY_TEXT = 60    # a title + meta description is still worth keeping
BATCH_SIZE = 64

# --- sources ----------------------------------------------------------------
# Official sites first. iti.gov.eg and depi.gov.eg are JavaScript single-page
# apps: the HTML they serve contains no programme text at all, only an empty app
# shell, so for those two we keep whatever the page really states (its title and
# meta description) and add other public pages that are actually readable -
# Mahara-Tech is ITI's own e-learning platform. Nothing here is hand-written
# programme information: if a
# source cannot be fetched it is skipped and reported, never replaced with
# invented tracks, durations or admission rules.
#
# `discover` follows links one level deep from that page, same domain only,
# limited to links whose text/URL looks like programme information. That is the
# whole crawling logic - no scraping framework, no queue, no browser.
SOURCES: dict[str, list[dict]] = {
    "iti": [
        {"url": "https://iti.gov.eg/iti/home",
         "title": "ITI Official Portal"},
        {"url": "https://maharatech.gov.eg/mod/page/view.php?id=14155",
         "title": "ITI Artificial Intelligence Academy for Everyone",
         "program": "AI Academy"},
        {"url": "https://maharatech.gov.eg/course/index.php",
         "title": "Mahara-Tech Course Categories (ITI e-learning platform)",
         "program": "Mahara-Tech"},
    ],
    "nti": [
        {"url": "https://nti.sci.eg/",
         "title": "NTI Official Portal", "discover": True},
        {"url": "https://nti.sci.eg/scientific_departments.html",
         "title": "NTI Scientific Departments"},
        {"url": "https://nti.sci.eg/dey/specialized_programs.html",
         "title": "NTI Digital Egypt Youth - Specialized Upskilling Programs",
         "program": "Digital Egypt Youth"},
        {"url": "https://nti.sci.eg/eta/",
         "title": "NTI Egyptian Talents Academy (ETA)",
         "program": "Egyptian Talents Academy"},
        {"url": "https://nti.sci.eg/prisummer/",
         "title": "NTI Private Summer Training Program",
         "program": "Private Summer Training"},
        {"url": "https://nti.sci.eg/prisummer/tracks.php",
         "title": "NTI Private Summer Training Tracks",
         "program": "Private Summer Training"},
        {"url": "https://nti.sci.eg/dey/HireReady.html",
         "title": "NTI HireReady Initiative", "program": "HireReady"},
        {"url": "https://nti.sci.eg/dey/creativa.html",
         "title": "NTI Creativa Innovation Hubs", "program": "Creativa"},
        {"url": "https://nti.sci.eg/vendor_academies.html",
         "title": "NTI International Vendor Academies", "program": "Vendor Academies"},
        {"url": "https://nti.sci.eg/wazeefa.html",
         "title": "NTI Wazeefa-Tech Initiative", "program": "Wazeefa-Tech"},
        {"url": "https://nti.sci.eg/contact_us.html",
         "title": "NTI Contact and Branch Locations"},
    ],
    "depi": [
        {"url": "https://depi.gov.eg/",
         "title": "DEPI Official Portal"},
        {"url": "https://depi.gov.eg/about",
         "title": "DEPI - About the Initiative"},
        {"url": "https://depi.gov.eg/tracks",
         "title": "DEPI - Tracks"},
    ],
    "itida": [
        {"url": "https://itida.gov.eg/English/Pages/about-itida.aspx",
         "title": "ITIDA - What We Do", "discover": True},
        {"url": "https://itida.gov.eg/English/Pages/Vision-Mission.aspx",
         "title": "ITIDA Vision and Mission"},
        {"url": "https://itida.gov.eg/English/Programs/StudentSummerTraining/Pages/default.aspx",
         "title": "ITIDA Student Summer Training", "program": "Student Summer Training"},
        {"url": "https://itida.gov.eg/english/programs/train-to-hire-program/pages/default.aspx",
         "title": "ITIDA Train to Hire Program", "program": "Train to Hire"},
        {"url": "https://itida.gov.eg/English/Programs/Graduation/Pages/default.aspx",
         "title": "ITIDA Graduation Projects Support", "program": "Graduation Projects"},
        {"url": "https://itida.gov.eg/English/Pages/FAQ.aspx",
         "title": "ITIDA Frequently Asked Questions"},
    ],
}

# Link text / URL fragments that mark a page as programme information.
DISCOVERY_KEYWORDS = (
    "program", "track", "course", "diploma", "training", "admission", "apply",
    "about", "faq", "department", "academy", "initiative", "eligib", "scholarship",
)
# Sign-in and account pages match "apply"/"registration" but hold no information.
EXCLUDED_URL_PARTS = (
    "login", "authenticate", "signin", "sign-in", "/user/", "registration",
    "_layouts", "logout", ".pdf", ".jpg", ".png",
)
_ZERO_WIDTH = re.compile("[​-‏﻿]")

# Navigation furniture that every page on a site repeats.
BOILERPLATE = {
    "home", "sign in", "log in", "login", "contact us", "read more", "skip",
    "turn on more accessible mode", "turn off more accessible mode",
    "facebook", "linkedin", "telegram", "instagram", "twitter", "youtube",
    "login to your account", "don't have an account?", "sign up!",
    "remember username", "lost password?", "page content", "page image",
}


# --- 1. collect -------------------------------------------------------------
def fetch_soup(url: str) -> BeautifulSoup | None:
    """GET a page and parse it. BeautifulSoup decodes the bytes itself, which
    respects the page's declared charset - guessing it (as `requests` does)
    turns Arabic pages into mojibake."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
    except Exception as e:
        print(f"    ! {type(e).__name__} for {url}")
        return None
    if response.status_code != 200:
        print(f"    ! HTTP {response.status_code} for {url}")
        return None
    return BeautifulSoup(response.content, "html.parser")


def readable_text(soup: BeautifulSoup) -> str:
    """Page text with navigation furniture and invisible padding dropped.

    The zero-width characters matter: SharePoint pages (itida.gov.eg) pad their
    content blocks with long runs of U+200B, which survive Unicode normalisation
    and count towards a chunk's length, so a chunk of nothing at all can look
    long enough to keep.
    """
    text = _ZERO_WIDTH.sub("", extract_clean_text(str(soup)))
    lines = [
        line for line in text.splitlines()
        if line.strip() and line.strip().lower() not in BOILERPLATE
    ]
    return "\n".join(lines)


def summary_text(soup: BeautifulSoup) -> str:
    """Title + meta description, for sites that render their content in JS.

    This is what the page itself declares about the organisation - still an
    official statement, just a short one - and it keeps the official URL in the
    knowledge base as a citable source.
    """
    parts = []
    if soup.title and soup.title.string:
        parts.append(soup.title.string.strip())
    for attrs in ({"name": "description"}, {"property": "og:description"}):
        tag = soup.find("meta", attrs=attrs)
        content = (tag.get("content") or "").strip() if tag else ""
        if content and content not in parts:
            parts.append(content)
    return "\n".join(parts)


def discover_links(home_url: str, soup: BeautifulSoup, limit: int = 8) -> list[dict]:
    """Same-domain links, one level deep, that look like programme information."""
    host = urlparse(home_url).netloc
    found, seen = [], {home_url}
    for anchor in soup.find_all("a", href=True):
        url = urljoin(home_url, anchor["href"]).split("#")[0]
        if url in seen or urlparse(url).netloc != host:
            continue
        if any(part in url.lower() for part in EXCLUDED_URL_PARTS):
            continue
        label = f"{anchor.get_text(' ', strip=True)} {url}".lower()
        if not any(keyword in label for keyword in DISCOVERY_KEYWORDS):
            continue
        seen.add(url)
        found.append({"url": url, "title": anchor.get_text(" ", strip=True) or url})
        if len(found) >= limit:
            break
    return found


def collect_data(org: str) -> list[dict]:
    """Fetch this organisation's public pages. Returns raw page dicts."""
    pages: list[dict] = []
    queue = list(SOURCES[org])
    visited: set[str] = set()
    # Several URLs on a single-page app serve the same shell, so the same text
    # arrives two or three times; keep the first one only.
    texts_seen: set[str] = set()

    while queue and len(pages) < MAX_PAGES_PER_ORG:
        source = queue.pop(0)
        url = source["url"]
        if url in visited:
            continue
        visited.add(url)

        soup = fetch_soup(url)
        time.sleep(REQUEST_DELAY)
        if soup is None:
            continue

        if source.get("discover"):
            queue.extend(
                link for link in discover_links(url, soup)
                if link["url"] not in visited
            )

        text = readable_text(soup)
        if len(text) < MIN_PAGE_TEXT:
            # A JavaScript app shell: keep what the page actually states.
            text = summary_text(soup)
            if len(text) < MIN_SUMMARY_TEXT:
                print(f"    - no readable content: {url}")
                continue

        fingerprint = _fingerprint(text)
        if fingerprint in texts_seen:
            print(f"    - same content as an earlier page: {url}")
            continue
        texts_seen.add(fingerprint)

        page = {
            "org": org,
            "document": f"{org.upper()}_Official_Web_Sources",
            "page": len(pages) + 1,
            "title": source.get("title") or url,
            "url": url,
            "source_type": "web",
            "text": text,
        }
        if source.get("program"):
            page["program"] = source["program"]
        pages.append(page)
        print(f"    + {len(text):6d} chars  {url}")

    return pages


# --- 2. clean ---------------------------------------------------------------
def clean_data(pages: list[dict]) -> list[dict]:
    """Same cleaning the PDF pipeline uses (whitespace + Unicode normalisation)."""
    cleaned = []
    for page in pages:
        text = clean_text(page["text"])
        if text:
            cleaned.append({**page, "text": text})
    return cleaned


# --- 3. chunk ---------------------------------------------------------------
def create_chunks(org: str, pages: list[dict]) -> list[dict]:
    """Same chunker the PDF pipeline uses, written to a NEW chunk file."""
    chunks = chunk_pages(pages)
    # chunk_pages only carries the fields the PDF pipeline needs; re-attach the
    # web-specific metadata from the page each chunk came from.
    by_page = {page["page"]: page for page in pages}
    for chunk in chunks:
        page = by_page.get(chunk.get("page"), {})
        chunk["source_type"] = "web"
        if page.get("program"):
            chunk["program"] = page["program"]

    # The same structuring the PDF chunks get: category, track, duration and
    # delivery mode, from 03_rag_pipeline/preprocessing/structure.py.
    chunks = structure_chunks(chunks)

    CHUNKS_FOLDER.mkdir(parents=True, exist_ok=True)
    output_path = CHUNKS_FOLDER / f"{org}_web_chunks.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    return chunks


# --- 3b. DEPI-only: chunk the structured API records without re-guessing them ---
def create_depi_structured_chunks(pages: list[dict]) -> list[dict]:
    """DEPI's counterpart to `create_chunks()`, for records built by `depi_api.py`.

    Two differences from the generic path, both deliberate:

    * No `chunk_pages()`. That function's sliding window exists to split long,
      unstructured prose (a PDF paragraph) into overlapping pieces; every page
      `depi_api.py` produces is already one bounded fact (one specialisation,
      one programme's duration statement, one track's overview) and splitting
      it further would only re-introduce the boundary-crossing risk this fix
      exists to remove. Each page becomes exactly one chunk.
    * No `structure_chunks()`. It re-derives category/track/duration/training_type
      from the chunk's own text with the same regexes used on the PDF catalogues,
      and would silently second-guess fields `depi_api.py` already knows are
      correct because it read them from the source's own table/field structure
      (see `depi_api.py`'s module docstring for why re-deriving them is worse,
      not just redundant).

    Still shares everything else with the generic path: same output file naming
    convention, same `chunk_metadata()`/`contextualize()` used for every other
    source, same upsert/prune logic in `add_to_vector_db()`.
    """
    chunks = []
    for index, page in enumerate(pages):
        chunk = dict(page)          # page IS the chunk; nothing to re-derive
        chunk.setdefault("page", index + 1)
        chunks.append(chunk)

    CHUNKS_FOLDER.mkdir(parents=True, exist_ok=True)
    output_path = CHUNKS_FOLDER / "depi_web_chunks.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    return chunks


# --- 4 + 5. embed and add to the existing vector DB -------------------------
def _fingerprint(text: str) -> str:
    return hashlib.sha1(" ".join(text.split()).encode("utf-8")).hexdigest()


def existing_fingerprints(collection) -> dict[str, str]:
    """text fingerprint -> id, for everything already in the collection."""
    stored = collection.get(include=["documents"])
    return {
        _fingerprint(text): chunk_id
        for chunk_id, text in zip(stored["ids"], stored["documents"])
        if text
    }


def prune_own_leftovers(org: str, collection, kept_ids: set[str]) -> int:
    """Drop ids from an earlier run of THIS script that the current run no longer
    produces - e.g. a page that has since been removed from the site.

    The id prefix is this script's own namespace (`<org>_web_chunks-`), so this
    can never reach a PDF chunk, a Q&A chunk, or anything embed_and_store.py
    wrote. Without it, a shorter run would leave the tail of the previous one
    behind as orphaned vectors.
    """
    prefix = f"{org}_web_chunks-"
    stale = [
        chunk_id for chunk_id in collection.get(include=[])["ids"]
        if chunk_id.startswith(prefix) and chunk_id not in kept_ids
    ]
    if stale:
        collection.delete(ids=stale)
    return len(stale)


def add_to_vector_db(org: str, chunks: list[dict], collection, known: dict[str, str]) -> tuple[int, int]:
    """Embed the new chunks and upsert them. Nothing else in the collection is touched.

    Text that some other source already contributed is skipped. Text this script
    itself stored on an earlier run is NOT skipped: it is re-stored under the id
    the current run gives it, because a page disappearing from a site shifts
    every later chunk's index, and treating the old copy as "already there"
    would drop the chunk and then prune the id it used to live at.
    """
    prefix = f"{org}_web_chunks-"
    ids, documents, metadatas, to_embed = [], [], [], []
    seen_this_run: set[str] = set()

    for index, chunk in enumerate(chunks):
        chunk_id = f"{prefix}{index}"
        fingerprint = _fingerprint(chunk["text"])
        owner = known.get(fingerprint)
        if fingerprint in seen_this_run:
            continue  # the same text twice in one run
        if owner is not None and not owner.startswith(prefix):
            continue  # already in the knowledge base from another source
        seen_this_run.add(fingerprint)
        known[fingerprint] = chunk_id
        ids.append(chunk_id)
        documents.append(chunk["text"])
        metadatas.append(chunk_metadata(chunk))
        to_embed.append(contextualize(chunk))

    if ids:
        embeddings: list[list[float]] = []
        for start in range(0, len(to_embed), BATCH_SIZE):
            embeddings.extend(embed_texts(to_embed[start:start + BATCH_SIZE]))
        collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    removed = prune_own_leftovers(org, collection, set(ids))
    return len(ids), removed


def save_raw(org: str, pages: list[dict]) -> Path:
    """Keep the raw pages next to the other sources, in their own folder."""
    output_path = RAW_FOLDER / org / "web" / f"{org}_web_info.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for page in pages:
            f.write(json.dumps(page, ensure_ascii=False) + "\n")
    return output_path


def process(org_name: str, collection, known: dict[str, str]) -> str:
    """One organisation, end to end. Returns a one-line report."""
    org = org_name.lower()
    print(f"\n--- {org_name} ---")

    # DEPI's own site is a JavaScript SPA that the generic requests+BeautifulSoup
    # crawler (`collect_data`) cannot read - it sees an empty shell. depi_api.py
    # goes straight to the JSON API that SPA itself calls, and already returns
    # fully structured, correctly-bounded records (see its module docstring), so
    # DEPI skips both the generic page crawler and the generic chunker.
    is_depi = org == "depi"
    pages = collect_depi_pages() if is_depi else collect_data(org)

    if not pages:
        raise RuntimeError("no readable pages could be fetched")

    pages = clean_data(pages)
    save_raw(org, pages)
    chunks = create_depi_structured_chunks(pages) if is_depi else create_chunks(org, pages)

    if is_depi:
        # `add_to_vector_db()`'s ids are positional ("depi_web_chunks-29" = the
        # chunk that was 30th in the list). Confirmed by direct test: Chroma's
        # `collection.upsert()` MERGES a metadata dict into whatever is already
        # stored at that id, rather than replacing it - so when this collector's
        # page count/order changes between runs (it has, twice, while this fix
        # was developed), an id that held "track=Management & ERP,
        # specialization=DevOps Engineer" in an old run can hand that
        # `specialization` value to an unrelated new chunk that happens to land
        # on the same id and never mentions DevOps Engineer at all - confirmed
        # happening in exactly this way during development. Clearing every
        # DEPI web-chunk id before inserting the fresh set removes the
        # possibility entirely, at the cost of DEPI's ids being reused rather
        # than reused as no-ops when content doesn't change. Scoped to the
        # `depi_web_chunks-` prefix only: this can never reach a PDF chunk, a
        # Q&A chunk, or any other organisation's vectors.
        stale = [i for i in collection.get(include=[])["ids"] if i.startswith("depi_web_chunks-")]
        if stale:
            collection.delete(ids=stale)
            for fingerprint in [fp for fp, owner in known.items() if owner in stale]:
                known.pop(fingerprint, None)

    added, removed = add_to_vector_db(org, chunks, collection, known)

    report = (f"[OK] {org_name} data collected "
              f"({len(pages)} pages, {len(chunks)} chunks, {added} vectors stored")
    return report + (f", {removed} stale removed)" if removed else ")")


def main(target_orgs: list[str] | None = None) -> int:
    orgs = target_orgs or ORGANIZATIONS
    print("=" * 70)
    print(f"Collecting public web information for {', '.join(orgs)}")
    print(f"Embedding model: {EMBEDDING_MODEL}")
    print("=" * 70)

    collection = get_collection()
    before = collection.count()
    print(f"Vector DB currently holds {before} chunks (these are kept as they are).")
    known = existing_fingerprints(collection)

    results, failed = [], []
    for org_name in orgs:
        # One organisation failing must not stop the others.
        try:
            results.append(process(org_name, collection, known))
        except Exception as e:
            failed.append(org_name)
            results.append(f"[FAIL] {org_name}: {type(e).__name__}: {e}")

    after = collection.count()
    print("\n" + "=" * 70)
    for line in results:
        print(line)
    print()
    if len(failed) < len(orgs):
        print(f"Vector DB updated successfully. {before} -> {after} chunks "
              f"(existing data untouched).")
    if failed:
        print(f"Organisations that failed: {', '.join(failed)}")
    print("=" * 70)
    return 1 if len(failed) == len(orgs) else 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--org", action="append", choices=[o.lower() for o in ORGANIZATIONS],
        help="Limit this run to one organisation (repeatable). Default: all four.",
    )
    args = parser.parse_args()
    sys.exit(main([o.upper() for o in args.org] if args.org else None))
