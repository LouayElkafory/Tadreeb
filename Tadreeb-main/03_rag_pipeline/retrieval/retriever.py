"""
Retrieval: find the chunks that can actually answer a question.

Three things this has to get right, each of which was previously wrong:

1. Distance scale. Chroma's default space is `l2` (squared euclidean), not
   cosine, so a threshold written for cosine distance rejected roughly half of
   all questions outright. The collection is now built with cosine distance
   (see vector_db_config) and thresholds here are cosine similarity, 0..1.

2. Arabic questions over an English corpus. A multilingual MiniLM only loosely
   aligns Egyptian Arabic questions with English catalogue text, so dense search
   alone missed term-precise questions ("DevOps مدته كام ساعة"). Dense and BM25
   results are fused, which recovers those.

3. Refusing honestly. Returning nothing is the correct answer for an
   out-of-corpus question, but returning nothing *because the threshold was
   miscalibrated* is how the generator ended up inventing answers. A chunk is
   kept when it is either semantically close or shares distinctive terms with
   the question, and the caller can tell the two apart via `score`.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "embeddings"))
from embedding_utils import embed_text
from vector_db_config import get_collection

from bm25 import BM25
from organizations import detect_organizations
from query_understanding import analyze
from reranker import rerank
from text_normalize import tokenize

TOP_K = 5
CANDIDATE_POOL = 30      # over-fetch from each retriever before fusing
RRF_K = 60               # standard reciprocal-rank-fusion damping constant

# --- relevance gating -------------------------------------------------------
# Deciding "the corpus cannot answer this" is done per QUESTION, not per chunk,
# using two signals, because neither separates on its own:
#
#   * vocabulary coverage - how many of the question's content terms exist
#     anywhere in the corpus. "ازاي اطبخ كشري" scores 0.0; a real question about
#     a programme scores high. This is the stronger signal.
#   * top cosine similarity - paraphrase-multilingual-MiniLM puts *any* two
#     Arabic sentences around 0.6-0.8, so this is only meaningful as a
#     tie-breaker for questions whose vocabulary is partly out of corpus.
#
# Thresholds are calibrated against 07_evaluation/test_questions.jsonl, which
# includes deliberately out-of-corpus questions. The negative set there is small,
# so re-run that evaluation after any corpus change rather than trusting these
# numbers indefinitely.
MIN_COVERAGE = float(os.getenv("RETRIEVAL_MIN_COVERAGE", "0.65"))
# A question whose vocabulary is only partly in the corpus still qualifies if
# the corpus has something *clearly* close - well above the ~0.78 similarity
# that this model assigns to any two unrelated Arabic sentences.
FALLBACK_COVERAGE = float(os.getenv("RETRIEVAL_FALLBACK_COVERAGE", "0.50"))
FALLBACK_SIMILARITY = float(os.getenv("RETRIEVAL_FALLBACK_SIMILARITY", "0.85"))
MIN_CHUNK_SIMILARITY = float(os.getenv("RETRIEVAL_MIN_CHUNK_SIMILARITY", "0.70"))
# When a question names an organisation, its own material should outrank another
# programme's near-identical wording. Applied as a ranking preference rather than
# a hard filter, so a genuinely better cross-programme chunk can still surface.
ORG_MATCH_BOOST = float(os.getenv("RETRIEVAL_ORG_MATCH_BOOST", "2.0"))
# The curated Q&A chunks are short and Arabic, so for an Arabic question they
# outscore the official documents almost every time and can fill every slot.
# They are derived material though - the PDFs are the authority - so a few slots
# are held for document chunks whenever any are relevant.
RESERVED_DOCUMENT_SLOTS = int(os.getenv("RETRIEVAL_RESERVED_DOCUMENT_SLOTS", "2"))
# Same reasoning one step further, for the web pages added by
# 01_scraping/collect_web_data.py. They broaden coverage - which is what makes a
# general "تفاصيل عن ITI" answerable - but a public web page is weaker evidence
# than the official PDF, and on 07_evaluation/test_questions.jsonl an unweighted
# corpus pushed two expected PDF chunks out of the top 5 (hit rate 87.1% ->
# 83.9%). At 0.7 the hit rate is back to 87.1%: web chunks still surface, but
# only when no document chunk answers the question as well.
WEB_SOURCE_WEIGHT = float(os.getenv("RETRIEVAL_WEB_SOURCE_WEIGHT", "0.7"))
# Global per-source-type multipliers for Q&A records and structured fact cards.
# Both default to 1.0 (neutral). Tried 0.55 / 1.8 so NTI's structured track list
# would outrank its Q&A records; measured on 07_evaluation/test_questions.jsonl
# that cost 87.1% -> 80.6% hit rate and MRR 0.66 -> 0.56, and a sweep of milder
# values found no pair that surfaced NTI's tracks without losing eval questions -
# a blanket boost also outranks the precise chunk a *specific* question needs.
# That goal is met instead by LIST_CARD reservation below, which only acts on
# list-type questions. Kept as env knobs for experiments.
QA_SOURCE_WEIGHT = float(os.getenv("RETRIEVAL_QA_SOURCE_WEIGHT", "1.0"))
STRUCTURED_SOURCE_BOOST = float(os.getenv("RETRIEVAL_STRUCTURED_SOURCE_BOOST", "1.0"))
# A card that lists an organisation's tracks in one chunk - a knowledge-base
# program card ("Tracks in this program: ...") or DEPI's "List of Tracks" page.
# For "what tracks does X offer?" it is the single most complete source, yet it
# often never enters the candidate pool: "إيه التراكات الموجودة في NTI؟" retrieved
# six Q&A/press chunks and none of NTI's six track names. Intents listed here get
# one slot reserved for the named organisation's best-matching list card.
LIST_CARD_INTENTS = {"tracks", "overview"}
_LIST_CARD_MARKERS = ("tracks in this program:", "list of tracks")
# A question asks about one *kind* of thing - a duration, an eligibility rule, a
# list of tracks - and `structure.py` tags every chunk with the categories it can
# answer. Preferring the matching category is what separates "how long is the Data
# Science track" from every other sentence that mentions Data Science. Applied as
# a ranking boost, never a filter: a chunk that answers the question without
# carrying the expected tag still surfaces.
CATEGORY_MATCH_BOOST = float(os.getenv("RETRIEVAL_CATEGORY_MATCH_BOOST", "1.6"))
# Naming a specific track or program is a much stronger signal than the category,
# because it rules out the other twenty-five tracks outright.
NAME_MATCH_BOOST = float(os.getenv("RETRIEVAL_NAME_MATCH_BOOST", "2.5"))

_bm25_cache: tuple[BM25, list[dict]] | None = None


def _load_corpus() -> tuple[BM25, list[dict]]:
    """Build (once) an in-memory BM25 index over everything in the collection."""
    global _bm25_cache
    if _bm25_cache is not None:
        return _bm25_cache

    collection = get_collection()
    stored = collection.get(include=["documents", "metadatas"])
    records = [
        {**(metadata or {}), "text": text}
        for text, metadata in zip(stored["documents"], stored["metadatas"])
    ]
    # Index the same contextual form that was embedded, so an org name mentioned
    # only in the metadata ("ITI") is still matchable as a term.
    index = BM25([tokenize(_contextualize(record)) for record in records])
    _bm25_cache = (index, records)
    return _bm25_cache


def reset_cache() -> None:
    """Drop the cached BM25 index (call after re-indexing the collection)."""
    global _bm25_cache
    _bm25_cache = None


def _contextualize(record: dict) -> str:
    """Chunk text prefixed with its source, matching how it was embedded."""
    parts = [
        str(record.get("org", "")).upper(),
        str(record.get("title") or record.get("document") or ""),
        record.get("text", ""),
    ]
    return "\n".join(part for part in parts if part)


def _term_overlap(query_terms: list[str], chunk_terms: set[str]) -> float:
    """Fraction of the question's content terms that appear in the chunk."""
    unique = set(query_terms)
    if not unique:
        return 0.0
    return sum(1 for term in unique if term in chunk_terms) / len(unique)


def vocabulary_coverage(query_terms: list[str], index: BM25) -> float:
    """Fraction of the question's content terms that occur anywhere in the corpus."""
    unique = set(query_terms)
    if not unique:
        return 0.0
    return sum(1 for term in unique if term in index.idf) / len(unique)


def _answerable(coverage: float, top_similarity: float) -> bool:
    """Whether the corpus plausibly contains an answer to this question at all."""
    if coverage >= MIN_COVERAGE:
        return True
    return coverage >= FALLBACK_COVERAGE and top_similarity >= FALLBACK_SIMILARITY


def retrieve(question: str, top_k: int | None = None, plan: dict | None = None) -> list[dict]:
    """Return the most relevant chunks for a question, best first.

    Returns an empty list when the corpus has nothing to say about the question,
    which the generator must treat as "I don't know" rather than answering
    unaided. Each chunk carries its source metadata plus `similarity` (cosine,
    0..1), `term_overlap` (0..1) and the fused `score` used for ordering.

    `plan` is the output of `query_understanding.analyze()`; it is computed here
    when the caller hasn't already done so. It decides what is actually searched
    for (the question plus the English terms its intent is written with) and how
    many chunks a question of that kind needs - a broad "tell me about ITI" is
    unanswerable from the 5 near-identical chunks a specific question wants.
    Passing `top_k` explicitly overrides that.
    """
    question = (question or "").strip()
    if not question:
        return []

    index, records = _load_corpus()
    if not records:
        return []

    plan = plan or analyze(question)
    search_text = plan.get("search_query") or question
    if top_k is None:
        top_k = plan.get("top_k", TOP_K)

    query_terms = tokenize(search_text)

    # --- dense half -------------------------------------------------------
    collection = get_collection()
    dense_hits: dict[int, float] = {}
    results = collection.query(
        query_embeddings=[embed_text(search_text)],
        n_results=min(CANDIDATE_POOL, len(records)),
        include=["documents", "distances"],
    )
    # Chroma returns documents, not corpus positions, so map back by text.
    position_of = {record["text"]: i for i, record in enumerate(records)}
    if results["documents"] and results["documents"][0]:
        for text, distance in zip(results["documents"][0], results["distances"][0]):
            position = position_of.get(text)
            if position is not None:
                dense_hits[position] = 1.0 - (distance / 2.0)  # cosine distance -> similarity

    top_similarity = max(dense_hits.values(), default=0.0)
    if not _answerable(vocabulary_coverage(query_terms, index), top_similarity):
        return []

    # --- lexical half -----------------------------------------------------
    lexical_scores = index.scores(query_terms)
    lexical_ranked = sorted(
        (i for i, s in enumerate(lexical_scores) if s > 0),
        key=lambda i: lexical_scores[i],
        reverse=True,
    )[:CANDIDATE_POOL]

    # --- reciprocal rank fusion ------------------------------------------
    dense_ranked = sorted(dense_hits, key=dense_hits.get, reverse=True)
    fused: dict[int, float] = {}
    for rank, position in enumerate(dense_ranked, start=1):
        fused[position] = fused.get(position, 0.0) + 1.0 / (RRF_K + rank)
    for rank, position in enumerate(lexical_ranked, start=1):
        fused[position] = fused.get(position, 0.0) + 1.0 / (RRF_K + rank)

    asked_about = plan.get("organizations") or detect_organizations(question)
    wanted_categories = set(plan.get("categories") or ())
    wanted_names = {
        field: plan[field]
        for field in ("track", "program", "specialization")
        if plan.get(field)
    }

    candidates = []
    for position, score in fused.items():
        record = records[position]
        similarity = dense_hits.get(position, 0.0)
        overlap = _term_overlap(query_terms, set(tokenize(_contextualize(record))))
        # Drop chunks that neither look close nor share any term with the
        # question - they would only pad the prompt with unrelated text.
        if similarity < MIN_CHUNK_SIMILARITY and overlap == 0.0:
            continue
        if asked_about and record.get("org") in asked_about:
            score *= ORG_MATCH_BOOST
        if record.get("source_type") == "web":
            score *= WEB_SOURCE_WEIGHT
        elif record.get("source_type") == "qa":
            score *= QA_SOURCE_WEIGHT
        elif record.get("source_type") == "structured":
            score *= STRUCTURED_SOURCE_BOOST
        if wanted_categories & _categories_of(record):
            score *= CATEGORY_MATCH_BOOST
        if _names_match(record, wanted_names):
            score *= NAME_MATCH_BOOST
        candidates.append({
            **record,
            "similarity": round(similarity, 4),
            "term_overlap": round(overlap, 4),
            "score": round(score, 6),
        })

    candidates.sort(key=lambda c: c["score"], reverse=True)
    candidates = _spread_across_sources(candidates, plan.get("max_per_source", 0))
    candidates = _spread_across_categories(candidates, plan.get("max_per_category", 0))
    if len(asked_about) > 1:
        candidates = _interleave_by_org(candidates, asked_about)
    selected = _diversify(candidates, top_k)
    if plan.get("intent") in LIST_CARD_INTENTS and asked_about:
        selected = _reserve_list_cards(selected, records, lexical_scores, asked_about, top_k)
    # No-op unless RERANKER_MODEL is configured (see reranker.py).
    return rerank(question, selected)


def _reserve_list_cards(selected: list[dict], records: list[dict], lexical_scores: list[float],
                        organizations: set[str], top_k: int) -> list[dict]:
    """Make sure each named organisation's track-listing card is in the context.

    The card is added at the end, replacing the weakest selected chunk only when
    the result is already full - so every stronger match keeps its place and
    rank, and a question that isn't a list question is never touched (see
    LIST_CARD_INTENTS).
    """
    present = {chunk.get("text") for chunk in selected}
    for org in sorted(organizations):
        cards = [
            i for i, record in enumerate(records)
            if record.get("org") == org
            and any(marker in (record.get("text", "") + " " + str(record.get("title", ""))).lower()
                    for marker in _LIST_CARD_MARKERS)
        ]
        if not cards:
            continue
        # Best lexical match to the question; the longer list breaks ties.
        best = max(cards, key=lambda i: (lexical_scores[i], records[i]["text"].count(",")))
        if records[best]["text"] in present:
            continue
        if len(selected) >= top_k:
            selected = selected[:-1]
        selected.append({**records[best], "similarity": 0.0,
                         "term_overlap": 0.0, "score": 0.0, "reserved": "list_card"})
        present.add(records[best]["text"])
    return selected


def _source_key(chunk: dict) -> tuple:
    return (chunk.get("document"), chunk.get("page"), chunk.get("title"))


def _categories_of(record: dict) -> set[str]:
    """Every category a chunk can answer (`structure.py` stores them comma-joined)."""
    joined = record.get("categories") or record.get("category") or ""
    return {part for part in str(joined).split(",") if part}


def _names_match(record: dict, wanted: dict[str, str]) -> bool:
    """Whether the chunk is about the track/program/specialisation that was named.

    Compared case-insensitively and in both directions, because the question may
    name the track more loosely than the document does ("Data Science" against
    "Data Science & AI") or the other way round.
    """
    for field, value in wanted.items():
        stored = str(record.get(field) or "").lower()
        target = value.lower()
        if stored and (stored in target or target in stored):
            return True
    return False


def _spread_across_sources(candidates: list[dict], max_per_source: int) -> list[dict]:
    """Cap how many chunks one page may contribute, keeping score order.

    Only broad questions set a cap. "عاوز أعرف تفاصيل عن ITI" used to come back
    as several fragments of whichever single page matched best, which is not an
    overview; capped, the same slots cover admission, tracks and duration.
    Capped-out chunks are appended rather than dropped, so nothing is lost if
    there aren't enough distinct sources to fill top_k.
    """
    if max_per_source <= 0:
        return candidates
    kept, overflow, counts = [], [], {}
    for chunk in candidates:
        key = _source_key(chunk)
        counts[key] = counts.get(key, 0) + 1
        (kept if counts[key] <= max_per_source else overflow).append(chunk)
    return kept + overflow


def _spread_across_categories(candidates: list[dict], max_per_category: int) -> list[dict]:
    """Cap how many chunks of one category a broad answer may use.

    An "overview" question asks for several kinds of fact at once, but the
    duration wording matches strongly enough to take every slot. Capping by
    category is what makes the eight chunks cover what the organisation is, its
    tracks, its duration and its admission rules instead of eight variations on
    one of them. Capped-out chunks are appended, not dropped.
    """
    if max_per_category <= 0:
        return candidates
    kept, overflow, counts = [], [], {}
    for chunk in candidates:
        category = chunk.get("category", "general")
        counts[category] = counts.get(category, 0) + 1
        (kept if counts[category] <= max_per_category else overflow).append(chunk)
    return kept + overflow


def _interleave_by_org(candidates: list[dict], organizations: set[str]) -> list[dict]:
    """For a comparison question, alternate between the organisations asked about.

    "إيه الفرق بين ITI وDEPI؟" matches ITI's material more strongly overall, so
    straight score order can fill every slot with ITI and leave the model
    nothing to compare against.
    """
    by_org: dict[str, list[dict]] = {org: [] for org in organizations}
    others: list[dict] = []
    for chunk in candidates:
        by_org.get(str(chunk.get("org", "")).lower(), others).append(chunk)

    interleaved = []
    queues = [q for q in by_org.values() if q]
    while queues:
        for queue in list(queues):
            interleaved.append(queue.pop(0))
            if not queue:
                queues.remove(queue)
    return interleaved + others


def _diversify(candidates: list[dict], top_k: int) -> list[dict]:
    """Take the top_k, but keep room for official-document chunks."""
    selected = candidates[:top_k]
    if RESERVED_DOCUMENT_SLOTS <= 0 or len(candidates) <= top_k:
        return selected

    def is_document(chunk: dict) -> bool:
        return chunk.get("source_type") != "qa"

    missing = RESERVED_DOCUMENT_SLOTS - sum(1 for c in selected if is_document(c))
    if missing <= 0:
        return selected

    promoted = [c for c in candidates[top_k:] if is_document(c)][:missing]
    if not promoted:
        return selected

    # Drop the weakest Q&A chunks to make room, then restore score order.
    qa_chunks = [c for c in selected if not is_document(c)]
    dropped = {id(c) for c in qa_chunks[-len(promoted):]}
    kept = [c for c in selected if id(c) not in dropped]
    return sorted(kept + promoted, key=lambda c: c["score"], reverse=True)
