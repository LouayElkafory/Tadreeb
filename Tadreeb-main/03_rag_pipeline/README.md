# 03_rag_pipeline

Turns the raw scraped text (`01_scraping`, stored under `02_data/01_raw/`)
into a searchable vector index, and answers retrieval queries from it at
generation time. This is the "Retrieval" half of RAG; `05_generation` is the
"Generation" half that consumes it.

## Structure

```
03_rag_pipeline/
├── preprocessing/
│   ├── clean_text.py     # raw text -> cleaned text
│   ├── deduplicate.py    # drop exact-duplicate pages
│   ├── chunker.py        # cleaned pages -> overlapping chunks
│   ├── qa_to_chunks.py   # curated Q&A pairs -> retrievable chunks
│   ├── structure.py      # a chunk -> its category, program, track, duration
│   └── build_knowledge_base.py  # the Organization -> Program -> Track hierarchy
├── embeddings/
│   ├── embedding_utils.py    # shared sentence-transformers model loader
│   ├── vector_db_config.py   # shared ChromaDB persistent client config
│   ├── embed_and_store.py    # embeds chunks and upserts them into ChromaDB
│   ├── backfill_structure.py # adds structured metadata + fact cards, no re-embed
│   └── model_benchmark.py    # placeholder - not implemented yet
└── retrieval/
    ├── retriever.py       # hybrid dense + lexical retrieval with a relevance gate
    ├── bm25.py            # in-memory BM25 index over the chunk corpus
    ├── text_normalize.py  # Arabic folding, light stemming, tokenisation
    ├── organizations.py   # detects which programme a question is about
    ├── query_understanding.py  # language, intent and query expansion, before retrieval
    └── reranker.py        # optional cross-encoder reranking (opt-in)
```

## How retrieval works

Retrieval combines two searches, because neither alone covers this corpus. The
documents are largely English PDF text; the questions are largely Egyptian
Arabic.

- **Dense** - the question is embedded with the same model used at indexing
  time and matched against ChromaDB. Good at paraphrase, weak at Arabic to
  English term matching.
- **Lexical (BM25)** - exact term matching over the same chunks. The terms that
  identify an answer ("DevOps", "DEPI", "Fortinet", "164") are written the same
  in both languages, so this finds what the embedding misses.

The two rankings are combined with reciprocal rank fusion. Before matching,
text on both sides goes through `text_normalize.py`, which folds Arabic
spelling variants (hamza forms, ta marbuta, alef maqsura, diacritics) and
strips clitics, so "مقر" matches "المقر".

If the question names a programme (`organizations.py`, including Arabic aliases
such as "المعهد القومي للاتصالات"), that programme's chunks are preferred -
otherwise a question about ITI is easily answered from NTI's near-identical
wording.

Finally, a couple of result slots are reserved for official-document chunks, so
an answer is never assembled purely from the derived Q&A material when the
source PDFs also have something to say. Web-collected chunks
(`01_scraping/collect_web_data.py`) are ranked slightly below the PDFs for the
same reason (`RETRIEVAL_WEB_SOURCE_WEIGHT`).

### The structured knowledge base (`preprocessing/structure.py`)

Each chunk carries the metadata that says what it can answer, not just where it
came from:

| Field | Example | Where it comes from |
| --- | --- | --- |
| `org` | `iti` | the source folder |
| `category` | `duration` | keyword scoring over the chunk (`structure.classify`) |
| `categories` | `duration,tracks,programs` | every category it scores on, comma-joined |
| `program` | `Professional Training Program` | matched literally against the names the corpus uses |
| `track` | `Data Science` | `"The <Name> Track ..."`, `"<NAME> TRACK"` |
| `specialization` | `DevOps Engineer` | DEPI's numbered job profiles |
| `duration` / `duration_unit` | `1,455 hours` | `TOTAL HOURS 1,455hrs`, `lasts for 120 hours`, `(4 Month)` |
| `training_type` | `blended` | ITI's `DELIVERY` field, or an explicit phrase about the training |
| `url` / `title` | source link and title | the scrapers |

Extraction is deterministic - regexes over patterns the documents actually use -
so nothing is invented. A field the sources never state is left missing, which is
what lets the chatbot answer "the sources don't say" instead of guessing.

Two things make the hierarchy real rather than implied:

* **Document rollup.** An ITI track brochure names its track on page 1 and states
  its hours in a table on page 3, so neither page answers "how long is the Data
  Science track" alone. Every page of a *single-subject* document inherits the
  document's program, track, duration and delivery mode. Documents covering
  several subjects are excluded, and that exclusion is load-bearing: NTI's portal
  describes six programs in one page and says "Train To Hire (4 Month)" in one of
  them - rolled up, the Creativa program card claimed a duration Creativa's
  sources never mention.
* **Fact cards.** `build_knowledge_base.py` writes
  `02_data/05_structured/<org>_knowledge.json` (the inspectable hierarchy) and one
  short card per program/track into `02_data/04_chunks/<org>_structured_chunks.jsonl`:

      ITI - Data Science track
      Organization: ITI (Information Technology Institute)
      Program: Professional Training Program
      Track: Data Science
      Training duration: 1,455 hours
      Training type / delivery mode: blended
      About: <verbatim excerpt from the brochure>
      Source document: 5.pdf

  Cards are indexed like any other chunk, and they are what a single-field
  question hits: "مدة تراك Data Science في ITI قد إيه؟" now returns the card
  first and the answer is one line.

### Understanding the question first (`query_understanding.py`)

Before any of the above runs, the question is read for its language and its
intent - one of **overview**, **comparison**, **duration**, **eligibility**,
**tracks** or **specific** - using a rule table over the same folded, stemmed
terms the lexical index uses. The intent decides two things:

- **Which chunk categories to prefer.** A duration question prioritises
  `category=duration`; an overview question asks for seven categories at once and
  caps how many chunks may share one, so the answer covers what the organisation
  is, its tracks, its duration and its admission rules instead of one of them
  eight times.
- **Which track or program the question is about.** Names are read from the
  knowledge-base files, so "مدة الـData Science track في ITI" resolves to
  `track=Data Science` and the other twenty-five ITI tracks stop competing.
- **How many chunks to retrieve.** A broad "عاوز أعرف تفاصيل عن ITI" gets 8 and
  a cap of 2 chunks per source page, so the answer covers admission, tracks and
  duration rather than repeating one paragraph. A specific question keeps the
  usual 5, undivided.
- **What is actually searched for.** A broad question carries almost no
  vocabulary that exists in a mostly-English corpus, so the English terms for
  its intent ("programs tracks duration eligibility target audience...") plus a
  small Arabic -> English glossary are appended to the query. Specific questions
  are searched for verbatim: padding them with generic programme terms measurably
  *lowers* their ranking.

Expansion only happens when the question names one of the four organisations.
Appending known-in-corpus English terms raises the vocabulary-coverage score, so
doing it unconditionally would let out-of-corpus questions past the refusal gate.

A comparison question naming two organisations gets its results interleaved
between them, so one programme's material cannot fill every slot.

The six intents are **overview**, **comparison**, **duration**,
**training_type**, **eligibility**, **application** and **tracks**, with
**specific** as the fallback.

This layer costs no LLM call. `05_generation/generate_answer.py` falls back to a
single Qwen translation of the question (`QUERY_TRANSLATION=auto`, the default)
only when retrieval still returns nothing.

### Deciding that a question is unanswerable

Returning nothing is the right answer for a question the corpus does not cover,
and it is what stops the generator inventing one. The gate is applied per
question, using:

- **vocabulary coverage** - the share of the question's content terms that
  appear anywhere in the corpus. This is the stronger signal.
- **top cosine similarity** - only used as a tie-breaker. The multilingual
  MiniLM scores *any* two Arabic sentences around 0.6-0.8, so an absolute
  similarity threshold on its own is not meaningful.

Thresholds (`RETRIEVAL_MIN_COVERAGE` and friends) are calibrated against
`07_evaluation/test_questions.jsonl`, which includes deliberately out-of-corpus
questions. **Re-run that evaluation after changing the corpus** - the negative
set is small and these numbers are not universal constants.

## Pipeline stages

1. **`preprocessing/clean_text.py`** - reads every
   `02_data/01_raw/<org>/official/*_raw.jsonl`, normalises Unicode, strips null
   bytes, diacritics and redundant whitespace, and writes one merged file per
   org: `02_data/03_processed/<org>_clean.jsonl`. It warns if any page still
   reads right-to-left reversed (see "Arabic PDFs" below) but never reverses
   text itself - at this stage the definite article and a lam-alef ligature are
   indistinguishable, so a blind repair corrupts good pages.

2. **`preprocessing/deduplicate.py`** - removes pages whose text is an exact
   repeat of an earlier page (repeated headers/footers/cover pages).

3. **`preprocessing/chunker.py`** - splits each cleaned page into
   sentence-aware chunks of up to 500 characters, with ~100 characters of
   trailing-sentence overlap. Each chunk keeps its page's
   `org`/`document`/`page`/`title`/`url` metadata.

4. **`preprocessing/qa_to_chunks.py`** - converts
   `02_data/02_qa_pairs/<org>_qa.jsonl` into
   `02_data/04_chunks/qa_chunks.jsonl`. These curated pairs are the main body
   of Arabic text in the corpus and are phrased the way users actually ask, so
   indexing them raises Arabic recall substantially. They are tagged
   `source_type: "qa"` so retrieval can tell derived material from the PDFs.

5. **`embeddings/embed_and_store.py`** - embeds every
   `02_data/04_chunks/*_chunks.jsonl` and upserts into the `tadreeb_chunks`
   collection. Each chunk is embedded **with a source header**
   (`DEPI / Technical Tracks Catalog / <text>`), because many catalogue chunks
   are bare fragments with nothing in the text naming the programme. The stored
   document is the raw text; only the vector uses the prefixed form. The
   collection is rebuilt from scratch on every run.

6. **`retrieval/retriever.py`** - see "How retrieval works" above.

## Shared config (`embeddings/`)

- **`embedding_utils.py`** - loads a `sentence-transformers` model (default
  `paraphrase-multilingual-MiniLM-L12-v2`, override with `EMBEDDING_MODEL`)
  once and caches it, so indexing and querying always use the same weights.
- **`vector_db_config.py`** - resolves `VECTOR_DB_PATH` and exposes
  `get_collection()` / `reset_collection()`. The collection is created with
  **cosine** distance. Chroma's default is `l2` (*squared* euclidean), which
  puts distances on a 0..4 scale; a threshold written for cosine distance
  against an l2 collection silently rejects most real matches.
  `get_collection()` warns if it opens an older collection built with the
  wrong space.

## Running

From the project root, in order:

```bash
python 03_rag_pipeline/preprocessing/clean_text.py
python 03_rag_pipeline/preprocessing/deduplicate.py
python 03_rag_pipeline/preprocessing/chunker.py
python 03_rag_pipeline/preprocessing/qa_to_chunks.py
python 03_rag_pipeline/embeddings/embed_and_store.py
```

Then check it:

```bash
python 07_evaluation/evaluate_retrieval.py
```

Re-run `embed_and_store.py` any time the chunks or the embedding model change -
it always rebuilds the collection rather than appending to a stale one.

## Tuning knobs

All optional; the defaults are what the evaluation above was calibrated with.

| Variable | Default | Effect |
| --- | --- | --- |
| `RETRIEVAL_MIN_COVERAGE` | `0.65` | Vocabulary coverage needed to attempt an answer. Raise to refuse more. |
| `RETRIEVAL_FALLBACK_COVERAGE` / `RETRIEVAL_FALLBACK_SIMILARITY` | `0.50` / `0.85` | Lets a partly-unfamiliar question through when the corpus has something clearly close. |
| `RETRIEVAL_MIN_CHUNK_SIMILARITY` | `0.70` | Floor for an individual chunk that shares no terms with the question. |
| `RETRIEVAL_ORG_MATCH_BOOST` | `2.0` | How strongly a named programme's own chunks are preferred. |
| `RETRIEVAL_RESERVED_DOCUMENT_SLOTS` | `2` | Result slots held for official-document chunks. |
| `RETRIEVAL_WEB_SOURCE_WEIGHT` | `0.7` | How far web-collected chunks are ranked below the official PDFs. `1.0` = no preference. |
| `RETRIEVAL_CATEGORY_MATCH_BOOST` | `1.6` | Preference for chunks whose category matches the question's intent. `1.0` ignores categories. |
| `RETRIEVAL_NAME_MATCH_BOOST` | `2.5` | Preference for chunks about the exact track/program the question names. |
| `QUERY_REWRITE` | `auto` | `always` also rewrites unanchored questions up front; `off` disables the LLM rewrite entirely. |
| `RERANKER_MODEL` | unset | Set to a cross-encoder (e.g. `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`) to enable reranking. |

## Arabic PDFs

PDF text extraction is done with **PyMuPDF** (`01_scraping/pdf_extractor.py`),
not pdfplumber. pdfplumber returns glyphs in the order they are painted, so an
Arabic page comes back visually reversed - "دمتعم بردم فلاآ" instead of
"آلاف مدرب معتمد". That text is meaningless to the embedding model and to the
LLM, so those pages retrieved nothing and pushed the model into making answers
up. PyMuPDF applies bidi reordering; pdfplumber remains as a per-page fallback.

**Known limitation:** the NTI Arabic press-release PDF embeds the lam-alef
ligature as two code points in the wrong order, so a few words come out
misspelled ("لالتصاالت" for "للاتصالات", "ثالث" for "ثلاث"). This is in the
PDF's own font encoding - no PyMuPDF extraction flag changes it, and it cannot
be repaired by a character rule afterwards, because word-internal "ال" is also
ordinary correct Arabic ("العالمي", "الالتزام"): a rule that fixes the broken
words corrupts the good ones. Affected: 2 pages of one document. To fix
properly, re-source that document as HTML (the NTI/MCIT web pages scrape
cleanly) or run OCR over it.

## Consumed by

`05_generation/generate_answer.py` imports `retrieve()` and treats an empty
result as "not in the sources" rather than answering unaided.
