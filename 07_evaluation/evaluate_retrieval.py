"""
Measures retrieval quality (Hit@K, MRR) for the RAG pipeline using ChromaDB.
"""
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "03_rag_pipeline" / "retrieval"))
from retriever import retrieve

TEST_FILE = PROJECT_ROOT / "07_evaluation" / "test_questions.jsonl"


def evaluate_retrieval(top_k: int = 3):
    if not TEST_FILE.exists():
        print(f"Test file not found: {TEST_FILE}")
        return

    with open(TEST_FILE, "r", encoding="utf-8") as f:
        test_cases = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(test_cases)} evaluation test questions.\n")
    print(f"{'#':<3} {'Question':<50} {'Expected Org':<14} {'Hit?':<6} {'Latency':<8}")
    print("-" * 85)

    hits = 0
    total_time = 0.0
    reciprocal_ranks = []

    for i, test in enumerate(test_cases, 1):
        q = test["question"]
        expected_org = test.get("expected_org", "").lower()
        expected_keywords = [k.lower() for k in test.get("expected_keywords", [])]

        t0 = time.perf_counter()
        try:
            chunks = retrieve(q, top_k=top_k)
        except Exception as e:
            chunks = []
            print(f"Retrieval error: {e}")
        latency = time.perf_counter() - t0
        total_time += latency

        # Check if expected org or any expected keyword is in retrieved chunks
        rank = 0
        hit = False
        for idx, chunk in enumerate(chunks, start=1):
            chunk_org = chunk.get("org", "").lower()
            chunk_text = chunk.get("text", "").lower()
            if (expected_org and expected_org in chunk_org) or any(k in chunk_text for k in expected_keywords):
                hit = True
                rank = idx
                break

        if hit:
            hits += 1
            reciprocal_ranks.append(1.0 / rank)
        else:
            reciprocal_ranks.append(0.0)

        hit_str = "✅ YES" if hit else "❌ NO"
        print(f"{i:<3} {q[:48]:<50} {expected_org:<14} {hit_str:<6} {latency*1000:6.1f}ms")

    hit_rate = (hits / len(test_cases)) * 100 if test_cases else 0
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0
    avg_latency = (total_time / len(test_cases)) * 1000 if test_cases else 0

    print("=" * 85)
    print(f"📊 SUMMARY REPORT (Top-{top_k}):")
    print(f"  • Hit Rate:     {hit_rate:.1f}% ({hits}/{len(test_cases)})")
    print(f"  • MRR:          {mrr:.3f}")
    print(f"  • Avg Latency:  {avg_latency:.1f}ms")
    print("=" * 85)


if __name__ == "__main__":
    evaluate_retrieval(top_k=3)
