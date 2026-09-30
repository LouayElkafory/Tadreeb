"""
Optional cross-encoder reranking of retrieved chunks.

Fusing dense and lexical results gets the right chunk into the top few, but the
ordering within those few is still decided by two scores that never actually
compared the question against the chunk text. A cross-encoder does exactly that,
and it is the most effective remaining lever on the questions this pipeline
still gets wrong - Arabic questions whose answer sits in the English handbook,
where neither embedding similarity nor term overlap carries much signal.

It is opt-in because it downloads a second model and adds real latency on CPU:

    RERANKER_MODEL=cross-encoder/mmarco-mMiniLMv2-L12-H384-v1

With the variable unset, `rerank` returns the input untouched, so retrieval
works fully without it.
"""
import os
from functools import lru_cache

RERANKER_MODEL = os.getenv("RERANKER_MODEL", "").strip()


@lru_cache(maxsize=1)
def get_reranker():
    """Load the cross-encoder once, or return None if it can't be loaded."""
    if not RERANKER_MODEL:
        return None
    try:
        from sentence_transformers import CrossEncoder
        return CrossEncoder(RERANKER_MODEL)
    except Exception as e:
        print(f"Warning: reranker '{RERANKER_MODEL}' unavailable ({e}); skipping reranking.")
        return None


def is_enabled() -> bool:
    return get_reranker() is not None


def rerank(question: str, chunks: list[dict], top_k: int | None = None) -> list[dict]:
    """Reorder chunks by cross-encoder relevance, best first.

    Returns the chunks unchanged when no reranker is configured, so callers can
    apply this unconditionally.
    """
    model = get_reranker()
    if model is None or len(chunks) < 2:
        return chunks[:top_k] if top_k else chunks

    try:
        scores = model.predict([(question, chunk.get("text", "")) for chunk in chunks])
    except Exception as e:
        print(f"Warning: reranking failed ({e}); keeping fusion order.")
        return chunks[:top_k] if top_k else chunks

    scored = [{**chunk, "rerank_score": float(score)} for chunk, score in zip(chunks, scores)]
    scored.sort(key=lambda c: c["rerank_score"], reverse=True)
    return scored[:top_k] if top_k else scored
