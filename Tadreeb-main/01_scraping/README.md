# 01_scraping

Collects the raw source material for the RAG pipeline: official program pages
for ITI, NTI, DEPI, and ITIDA, plus their official PDFs. Everything here
writes into `02_data/01_raw/<org>/official/`, which `03_rag_pipeline` then
cleans, deduplicates, and chunks.

## Files

| File | Purpose |
| --- | --- |
| `scraper_utils.py` | Shared helpers used by every scraper: `fetch_url` (HTTP GET with retries and a browser User-Agent), `extract_clean_text` (strips scripts/nav/footers from HTML and normalizes whitespace), `save_pages_jsonl` (writes a list of page dicts to JSONL). |
| `scrape_iti.py` | Scrapes the ITI official portal (tracks, admission process, program pages). Falls back to a bundled Arabic summary of ITI's programs/admission rules if the live pages can't be fetched (e.g. blocked by Cloudflare). Writes `02_data/01_raw/iti/official/iti_web_raw.jsonl`. |
| `scrape_nti.py` | Scrapes the NTI official portal. Writes `02_data/01_raw/nti/official/nti_web_raw.jsonl`. |
| `scrape_depi.py` | Scrapes the DEPI official portal. Writes `02_data/01_raw/depi/official/depi_web_raw.jsonl`. |
| `scrape_itida.py` | Scrapes ITIDA's initiative pages. Writes `02_data/01_raw/itida/official/itida_web_raw.jsonl`. |
| `collect_web_data.py` | **Run on its own with `python collect_web_data.py`.** Collects general public information (programs, tracks, durations, eligibility, target audience, application info) about all four organisations in one run, then cleans, chunks, embeds and **adds** it to the existing ChromaDB collection. Incremental by design: it reuses the existing `clean_text()`, `chunk_pages()` and embedding code, never calls `reset_collection()`, and writes to new files only. See "Web data collection" below. |
| `pdf_extractor.py` | Extracts per-page raw text (via **PyMuPDF**, with `pdfplumber` as a per-page fallback) from every PDF already sitting in `02_data/01_raw/<org>/official/`, and writes `<org>_raw.jsonl` next to them. This is the PDF counterpart to the web scrapers above - it doesn't download anything, it only reads PDFs that were manually placed there. See "Arabic PDFs" below. |
| `text_order.py` | Detects Arabic text extracted in visual (painted) order rather than logical reading order. Shared by the extractor and `03_rag_pipeline/preprocessing/clean_text.py` so both agree on what broken text looks like. |
| `run_all_scrapers.py` | Orchestrates the full ingestion pipeline in order: run all four web scrapers -> `pdf_extractor.py` -> `03_rag_pipeline/preprocessing/clean_text.py` -> `deduplicate.py` -> `chunker.py` -> `03_rag_pipeline/embeddings/embed_and_store.py`. |
| `scrape_facebook_pages.py` | Placeholder - not implemented yet. Intended to collect posts/comments from official Facebook pages as a source for fine-tuning questions. |
| `scheduler.py` | Placeholder - not implemented yet. Intended to periodically re-run the web scrapers so RAG data stays current (fine-tuning data doesn't need the same refresh cadence). |

## Web data collection (`collect_web_data.py`)

```
Official Web Sources -> Collect -> Clean -> Chunk -> Embed -> Add New Vectors
                                                                   |
                                                          Existing Vector DB
```

Run it from this folder:

```bash
python collect_web_data.py
```

Every run processes **ITI, NTI, DEPI and ITIDA**. If one organisation fails the
others still run, and the summary at the end says which succeeded:

```
[OK] ITI data collected (3 pages, 28 chunks, 28 vectors stored)
[OK] NTI data collected (9 pages, 151 chunks, 117 vectors stored)
[OK] DEPI data collected (1 pages, 1 chunks, 1 vectors stored)
[OK] ITIDA data collected (12 pages, 229 chunks, 229 vectors stored)

Vector DB updated successfully. 1262 -> 1637 chunks (existing data untouched).
```

**What it writes** (all new paths - nothing existing is overwritten):

| Path | Contents |
| --- | --- |
| `02_data/01_raw/<org>/web/<org>_web_info.jsonl` | The collected pages. A new `web/` folder, deliberately outside the `*/official/*_raw.jsonl` glob that `clean_text.py` reads, so the existing cleaning/chunking output is unchanged. |
| `02_data/04_chunks/<org>_web_chunks.jsonl` | The chunks. These *do* match the `*_chunks.jsonl` glob `embed_and_store.py` uses, on purpose: a later full rebuild re-indexes the web data with the same ids instead of losing it. |
| ChromaDB | New vectors, added with `collection.upsert()`. |

**Metadata** stored on every web chunk, using the field names the rest of the
pipeline already reads (`06_app/api.py` builds its source cards from these):

| Requested field | Stored as | Example |
| --- | --- | --- |
| organization | `org` | `itida` |
| program | `program` | `Train to Hire` |
| source_url | `url` | `https://itida.gov.eg/...` |
| title | `title` | `ITIDA Train to Hire Program` |
| source_type | `source_type` | `web` |

Chunks additionally get the structured fields every other chunk gets from
`03_rag_pipeline/preprocessing/structure.py` - `category`, `track`, `duration`,
`training_type` - so web pages are searchable by category in exactly the same way
as the PDFs.

**Duplicates and re-runs.** Chunk ids are deterministic (`<org>_web_chunks-<n>`),
so a re-run updates a chunk in place rather than adding a second copy. Text that
another source already contributed is skipped, and leftovers from a longer
earlier run are pruned - only within this script's own id prefix, never anything
`embed_and_store.py` wrote.

**No invented content.** `iti.gov.eg` and `depi.gov.eg` are JavaScript
single-page apps that serve no programme text to a plain HTTP client. For those,
the script keeps what the page itself declares (its title and meta description)
and draws the rest from other readable public sources - Mahara-Tech, which is
ITI's own e-learning platform, and Wikipedia. A page that cannot be read is
skipped and reported; it is never replaced with hand-written tracks, durations
or admission rules.

**Retrieval weighting.** Web chunks are ranked slightly below the official PDFs
(`RETRIEVAL_WEB_SOURCE_WEIGHT`, default 0.7) so a public web page never displaces
the official document when both answer the question. Re-run
`07_evaluation/evaluate_retrieval.py` after changing it.

## Output

Each scraper/extractor writes JSONL, one JSON object per line, with the
fields `org`, `document`, `page`, `text` (web scrapers also include `url`
and `title`):

```
02_data/01_raw/
├── iti/official/iti_web_raw.jsonl      (scrape_iti.py)
├── iti/official/iti_raw.jsonl          (pdf_extractor.py, from PDFs in this folder)
├── nti/official/nti_web_raw.jsonl
├── depi/official/depi_web_raw.jsonl
└── itida/official/itida_web_raw.jsonl
```

## Running

Each scraper can be run standalone (from inside `01_scraping/`, since they
import `scraper_utils` as a sibling module):

```bash
cd 01_scraping
python scrape_iti.py
python scrape_nti.py
python scrape_depi.py
python scrape_itida.py
python pdf_extractor.py
```

Or run the whole ingestion pipeline (scraping through embedding) in one go:

```bash
cd 01_scraping
python run_all_scrapers.py
```

## Notes

- Every web scraper degrades gracefully: if a site can't be reached (network
  issue, Cloudflare, layout change), it falls back to a bundled Arabic summary
  so downstream stages always have something to work with instead of failing.
- `pdf_extractor.py` never fetches PDFs itself - PDFs must already exist under
  `02_data/01_raw/<org>/official/` before running it.
- No dependencies are installed by anything in this folder; scraping needs
  `requests`, `beautifulsoup4`, `PyMuPDF`, and `pdfplumber` (see the project-root
  `requirements.txt`).

## Arabic PDFs

PDF extraction uses PyMuPDF rather than pdfplumber. pdfplumber returns glyphs
in the order they are painted on the page, so an Arabic (right-to-left) page
comes back reversed - "دمتعم بردم فلاآ" instead of "آلاف مدرب معتمد". Reversed
text is meaningless to the embedding model and to the LLM: those pages matched
nothing during retrieval, and when one did reach the prompt it gave the model
nothing usable, which is a direct route to an invented answer. PyMuPDF applies
bidi reordering and returns logical order.

`text_order.is_visually_ordered()` guards against regressions: the extractor
warns per page if the output still reads backwards, and the cleaning step warns
again if such a page reaches it. If you ever see that warning, re-run
`pdf_extractor.py` rather than trying to repair the text downstream - see the
"Arabic PDFs" section of `03_rag_pipeline/README.md` for why a character-level
repair is not safe.
