"""
End-to-end evaluation for Tadreeb AI generation: groundedness, refusal, and memory.

"Grounded" here means the answer actually contains a fact from the expected
sources. The previous check passed any answer longer than 30 characters that had
sources attached, which a fluent hallucination satisfies easily.

The refusal section matters just as much: for a question the corpus cannot
answer, the only correct behaviour is to say so.
"""
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "05_generation"))
from generate_answer import NO_CONTEXT_MESSAGE, generate_answer

# These scripts print Arabic. On Windows the console defaults to a legacy code
# page (cp1256/cp437) that cannot encode it, and printing raises UnicodeEncodeError
# part-way through a run. Force UTF-8 on our own streams.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TEST_FILE = PROJECT_ROOT / "07_evaluation" / "test_questions.jsonl"
REFUSAL_MARKER = "مش لاقي معلومات"


def is_refusal(answer: str) -> bool:
    return REFUSAL_MARKER in answer or answer.strip() == NO_CONTEXT_MESSAGE.strip()


def evaluate_end_to_end(limit: int | None = None):
    with open(TEST_FILE, "r", encoding="utf-8") as f:
        test_cases = [json.loads(line) for line in f if line.strip()]

    answerable = [t for t in test_cases if not t.get("expect_no_results")]
    unanswerable = [t for t in test_cases if t.get("expect_no_results")]
    if limit:
        answerable = answerable[:limit]

    print("=" * 64)
    print("PART 1: Groundedness on answerable questions")
    print("=" * 64)

    grounded = 0
    wrongly_refused = 0
    total_time = 0.0

    for i, test in enumerate(answerable, 1):
        question = test["question"]
        keywords = [k.lower() for k in test.get("expected_keywords", [])]

        start = time.perf_counter()
        result = generate_answer(question)
        latency = time.perf_counter() - start
        total_time += latency

        answer = result.get("answer", "")
        sources = result.get("sources", [])

        if is_refusal(answer):
            wrongly_refused += 1
            status = "REFUSED"
        elif sources and any(k in answer.lower() for k in keywords):
            grounded += 1
            status = "GROUNDED"
        elif sources:
            status = "UNVERIFIED"   # answered with sources, but no expected fact in it
        else:
            status = "NO SOURCES"

        print(f"\n[{i}] {question}")
        print(f"    {status} | {latency:.1f}s | {len(sources)} source(s)")
        print(f"    {answer[:160]}")

    print("\n" + "=" * 64)
    print("PART 2: Refusal on out-of-corpus questions")
    print("=" * 64)
    correct_refusals = 0
    for test in unanswerable:
        result = generate_answer(test["question"])
        refused = is_refusal(result["answer"])
        correct_refusals += refused
        print(f"  {'OK  ' if refused else 'FAIL'} {test['question'][:44]} -> {result['answer'][:70]}")

    print("\n" + "=" * 64)
    print("PART 3: Multi-turn conversational memory")
    print("=" * 64)
    first_question = "احكيلي عن برامج معهد تكنولوجيا المعلومات ITI"
    r1 = generate_answer(first_question)
    history = [
        {"role": "user", "content": first_question},
        {"role": "assistant", "content": r1["answer"]},
    ]
    print(f"  Turn 1: {r1['answer'][:100]}")

    followup = "طب إيه شروط التقديم فيها؟"
    r2 = generate_answer(followup, history=history)
    followup_ok = any(s.get("org") == "iti" for s in r2.get("sources", []))
    print(f"  Turn 2 (follow-up): {r2['answer'][:100]}")
    print(f"    resolved to ITI sources: {'YES' if followup_ok else 'NO'}")

    history += [
        {"role": "user", "content": followup},
        {"role": "assistant", "content": r2["answer"]},
    ]
    r3 = generate_answer("أنا سألتك في أول سؤال عن إيه؟", history=history)
    memory_ok = "ITI" in r3["answer"] or "معهد تكنولوجيا" in r3["answer"]
    print(f"  Turn 3 (memory): {r3['answer'][:120]}")
    print(f"    recalled first question: {'YES' if memory_ok else 'NO'}")

    print("\n" + "=" * 64)
    print("SUMMARY")
    print(f"  Grounded answers:     {grounded}/{len(answerable)}")
    print(f"  Wrongly refused:      {wrongly_refused}/{len(answerable)}")
    print(f"  Correct refusals:     {correct_refusals}/{len(unanswerable)}")
    print(f"  Follow-up resolution: {'PASS' if followup_ok else 'FAIL'}")
    print(f"  Conversation memory:  {'PASS' if memory_ok else 'FAIL'}")
    print(f"  Avg latency:          {total_time/len(answerable):.1f}s")
    print("=" * 64)


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    evaluate_end_to_end(limit)
