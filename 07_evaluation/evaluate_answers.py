"""
End-to-End Evaluation for Tadreeb AI generation (Style, Groundedness, Conversational Memory).
"""
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "05_generation"))
from generate_answer import generate_answer

TEST_FILE = PROJECT_ROOT / "07_evaluation" / "test_questions.jsonl"


def evaluate_end_to_end():
    print("================================================================")
    print("🧪 PART 1: Evaluating Standard Q&A Groundedness")
    print("================================================================")
    with open(TEST_FILE, "r", encoding="utf-8") as f:
        test_cases = [json.loads(line) for line in f if line.strip()]

    total_time = 0.0
    grounded_count = 0

    for i, test in enumerate(test_cases, 1):
        q = test["question"]
        expected_keywords = [k.lower() for k in test.get("expected_keywords", [])]

        t0 = time.perf_counter()
        result = generate_answer(q)
        latency = time.perf_counter() - t0
        total_time += latency

        answer = result.get("answer", "")
        sources = result.get("sources", [])

        # Check if answer mentions expected keywords or provides sources
        has_keywords = any(k in answer.lower() for k in expected_keywords)
        is_grounded = len(sources) > 0 and (has_keywords or len(answer) > 30)
        if is_grounded:
            grounded_count += 1

        status = "✅ PASS" if is_grounded else "⚠️ REVIEW"
        print(f"\n[Test {i}] {q}")
        print(f"Status: {status} | Latency: {latency:.2f}s | Sources: {len(sources)}")
        print(f"Answer snippet: {answer[:140]}...")

    print("\n================================================================")
    print("🧠 PART 2: Evaluating Multi-Turn Conversational Memory")
    print("================================================================")
    # Turn 1
    t1_question = "احكيلي عن برامج معهد تكنولوجيا المعلومات ITI"
    print(f"\n[Turn 1] User: {t1_question}")
    r1 = generate_answer(t1_question)
    print(f"Assistant: {r1['answer'][:120]}...")

    history = [
        {"role": "user", "content": t1_question},
        {"role": "assistant", "content": r1["answer"]},
    ]

    # Turn 2: Follow-up using pronoun ("فيها")
    t2_question = "طب إيه شروط التقديم فيها؟"
    print(f"\n[Turn 2] User: {t2_question}")
    r2 = generate_answer(t2_question, history=history)
    print(f"Assistant: {r2['answer'][:120]}...")

    history.append({"role": "user", "content": t2_question})
    history.append({"role": "assistant", "content": r2["answer"]})

    # Turn 3: Memory check ("أول سؤال")
    t3_question = "أنا سألتك في أول سؤال عن إيه؟"
    print(f"\n[Turn 3] User: {t3_question}")
    r3 = generate_answer(t3_question, history=history)
    print(f"Assistant: {r3['answer']}")

    memory_passed = "ITI" in r3["answer"] or "معهد تكنولوجيا المعلومات" in r3["answer"] or "احكيلي" in r3["answer"]
    print(f"\nConversational Memory Test: {'✅ PASSED' if memory_passed else '❌ FAILED'}")

    print("\n================================================================")
    print(f"📊 Overall Groundedness Score: {grounded_count}/{len(test_cases)} ({(grounded_count/len(test_cases))*100:.1f}%)")
    print(f"⚡ Average Generation Latency: {total_time/len(test_cases):.2f}s")
    print("================================================================")


if __name__ == "__main__":
    evaluate_end_to_end()
