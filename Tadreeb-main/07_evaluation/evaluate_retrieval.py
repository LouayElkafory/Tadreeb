"""
Measures retrieval quality (Hit@K, MRR, and refusal accuracy) for the RAG pipeline.

A "hit" requires an expected keyword to appear in the retrieved text. Matching on
the expected organisation alone - as this used to - is nearly free with only four
organisations in the corpus, so it reported a high score while the pipeline was
returning nothing useful.

Questions marked `expect_no_results` are deliberately outside the corpus. They
check the opposite failure: retrieval that returns something for an unanswerable
question is what pushes the generator into making an answer up.
"""
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "03_rag_pipeline" / "retrieval"))
from retriever import retrieve

# These scripts print Arabic. On Windows the console defaults to a legacy code
# page (cp1256/cp437) that cannot encode it, and printing raises UnicodeEncodeError
# part-way through a run. Force UTF-8 on our own streams.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TEST_FILE = PROJECT_ROOT / "07_evaluation" / "test_questions.jsonl"


def chunk_matches(chunk: dict, keywords: list[str]) -> bool:
    text = chunk.get("text", "").lower()
    return any(keyword in text for keyword in keywords)


def evaluate_retrieval(top_k: int = 5):
    if not TEST_FILE.exists():
        print(f"Test file not found: {TEST_FILE}")
        return

    with open(TEST_FILE, "r", encoding="utf-8") as f:
        test_cases = [json.loads(line) for line in f if line.strip()]

    answerable = [t for t in test_cases if not t.get("expect_no_results")]
    unanswerable = [t for t in test_cases if t.get("expect_no_results")]

    print(f"Loaded {len(test_cases)} test questions "
          f"({len(answerable)} answerable, {len(unanswerable)} out-of-corpus).\n")
    print(f"{'#':<3} {'Question':<48} {'Org':<7} {'Hit':<6} {'Rank':<5} {'Latency':<9}")
    print("-" * 84)

    hits = 0
    reciprocal_ranks = []
    total_time = 0.0

    for i, test in enumerate(answerable, 1):
        question = test["question"]
        keywords = [k.lower() for k in test.get("expected_keywords", [])]

        start = time.perf_counter()
        try:
            chunks = retrieve(question, top_k=top_k)
        except Exception as e:
            chunks = []
            print(f"Retrieval error: {e}")
        latency = time.perf_counter() - start
        total_time += latency

        rank = next((idx for idx, c in enumerate(chunks, 1) if chunk_matches(c, keywords)), 0)
        if rank:
            hits += 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)

        print(f"{i:<3} {question[:46]:<48} {test.get('expected_org', ''):<7} "
              f"{('YES' if rank else 'NO'):<6} {(rank or '-'):<5} {latency*1000:7.1f}ms")

    print("-" * 84)
    correct_refusals = 0
    for test in unanswerable:
        chunks = retrieve(test["question"], top_k=top_k)
        refused = not chunks
        correct_refusals += refused
        status = "refused" if refused else f"returned {len(chunks)} chunk(s)"
        print(f"    out-of-corpus: {test['question'][:44]:<46} -> {status}")

    hit_rate = (hits / len(answerable)) * 100 if answerable else 0
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0
    avg_latency = (total_time / len(answerable)) * 1000 if answerable else 0
    refusal_rate = (correct_refusals / len(unanswerable)) * 100 if unanswerable else 0

    print("=" * 84)
    print(f"SUMMARY (Top-{top_k}):")
    print(f"  Hit Rate:           {hit_rate:.1f}%  ({hits}/{len(answerable)})")
    print(f"  MRR:                {mrr:.3f}")
    print(f"  Correct refusals:   {refusal_rate:.1f}%  ({correct_refusals}/{len(unanswerable)})")
    print(f"  Avg latency:        {avg_latency:.1f}ms")
    print("=" * 84)
    return {"hit_rate": hit_rate, "mrr": mrr, "refusal_rate": refusal_rate}


if __name__ == "__main__":
    evaluate_retrieval(top_k=5)
