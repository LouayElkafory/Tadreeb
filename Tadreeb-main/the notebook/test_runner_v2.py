"""
Test Runner v2 - Simplified Test Execution
"""
import requests
import json
from datetime import datetime

API_URL = "http://localhost:8001/api/chat"

# Test cases
TEST_CASES = [
    {"id": 1, "lang": "EN", "category": "Program", "msg": "What is the HireReady program?"},
    {"id": 2, "lang": "AR", "category": "Program", "msg": "ما هي مبادرة رواد مصر الرقمية؟"},
    {"id": 3, "lang": "EN", "category": "Eligibility", "msg": "What are the eligibility criteria?"},
    {"id": 4, "lang": "AR", "category": "Eligibility", "msg": "ما هي شروط التقديم؟"},
    {"id": 5, "lang": "EN", "category": "Duration", "msg": "How long is the training?"},
    {"id": 6, "lang": "AR", "category": "Duration", "msg": "كام ساعة التدريب يومياً؟"},
    {"id": 7, "lang": "EN", "category": "Tracks", "msg": "What are the available tracks?"},
    {"id": 8, "lang": "AR", "category": "Tracks", "msg": "إيه التراكات المتاحة؟"},
    {"id": 9, "lang": "EN", "category": "Jobs", "msg": "Does it help with job placement?"},
    {"id": 10, "lang": "AR", "category": "Jobs", "msg": "هل في مساعدة في إيجاد وظيفة؟"},
    {"id": 11, "lang": "EN", "category": "Fees", "msg": "Is the training free?"},
    {"id": 12, "lang": "AR", "category": "Fees", "msg": "هل البرنامج مجاني؟"},
    {"id": 13, "lang": "EN", "category": "Dates", "msg": "When is the deadline?"},
    {"id": 14, "lang": "AR", "category": "Dates", "msg": "متى موعد التقديم؟"},
    {"id": 15, "lang": "EN", "category": "Skills", "msg": "What skills are needed?"},
    {"id": 16, "lang": "AR", "category": "Skills", "msg": "ما المهارات اللي أحتاجها؟"},
    {"id": 17, "lang": "EN", "category": "Employees", "msg": "Can employees participate?"},
    {"id": 18, "lang": "AR", "category": "Employees", "msg": "هل الموظفين ممكن يشتركوا؟"},
    {"id": 19, "lang": "EN", "category": "Contact", "msg": "How do I contact?"},
    {"id": 20, "lang": "AR", "category": "Contact", "msg": "ما رقم التواصل؟"},
]

def run_tests():
    """Execute all 20 tests."""
    print("\n" + "="*100)
    print("🧪 TADREEB FAISS RAG API - 20 TEST CASES (SIMPLIFIED)")
    print("="*100 + "\n")

    passed = 0
    failed = 0
    results = []

    for i, test in enumerate(TEST_CASES, 1):
        try:
            # Send request
            response = requests.post(
                API_URL,
                json={"message": test["msg"], "conversation_id": None},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            # Validate
            chunk_count = data.get("chunk_count", 0)
            sources_count = len(data.get("sources", []))
            avg_score = data.get("avg_score", 0)

            success = (
                chunk_count == 3 and
                sources_count == 3 and
                avg_score > 0.001
            )

            status = "✅ PASS" if success else "❌ FAIL"
            if success:
                passed += 1
            else:
                failed += 1

            # Display
            print(f"Test {i:2d} | {status} | {test['lang']} | {test['category']:12} | "
                  f"Chunks: {chunk_count}/3 | Score: {avg_score:.6f} | Time: {response.elapsed.total_seconds():.2f}s")

            results.append({
                "test_id": test["id"],
                "status": "PASS" if success else "FAIL",
                "language": test["lang"],
                "category": test["category"],
                "message": test["msg"],
                "chunks": chunk_count,
                "sources": sources_count,
                "avg_score": avg_score,
                "response_time": response.elapsed.total_seconds()
            })

        except Exception as e:
            print(f"Test {i:2d} | ❌ ERROR | {test['lang']} | {test['category']:12} | {str(e)[:40]}")
            failed += 1
            results.append({
                "test_id": test["id"],
                "status": "ERROR",
                "error": str(e)
            })

    # Summary
    print("\n" + "="*100)
    print("📊 SUMMARY")
    print("="*100)
    print(f"\n✅ PASSED: {passed}/20 ({passed*5}%)")
    print(f"❌ FAILED: {failed}/20 ({failed*5}%)")

    # By category
    cats = {}
    for r in results:
        if "category" in r:
            cat = r["category"]
            if cat not in cats:
                cats[cat] = {"pass": 0, "fail": 0}
            if r["status"] == "PASS":
                cats[cat]["pass"] += 1
            else:
                cats[cat]["fail"] += 1

    print(f"\n📂 BY CATEGORY:")
    for cat in sorted(cats.keys()):
        stats = cats[cat]
        total = stats["pass"] + stats["fail"]
        status = "✅" if stats["pass"] == total else "⚠️"
        print(f"   {status} {cat:15} {stats['pass']}/{total}")

    # By language
    langs = {"EN": 0, "AR": 0}
    lang_pass = {"EN": 0, "AR": 0}
    for r in results:
        if "language" in r:
            lang = r["language"]
            langs[lang] += 1
            if r["status"] == "PASS":
                lang_pass[lang] += 1

    print(f"\n🌐 BY LANGUAGE:")
    for lang in sorted(langs.keys()):
        status = "✅" if lang_pass[lang] == langs[lang] else "⚠️"
        print(f"   {status} {lang:10} {lang_pass[lang]}/{langs[lang]}")

    # Performance
    times = [r["response_time"] for r in results if "response_time" in r]
    if times:
        print(f"\n⏱️  PERFORMANCE:")
        print(f"   Average: {sum(times)/len(times):.3f}s")
        print(f"   Min:     {min(times):.3f}s")
        print(f"   Max:     {max(times):.3f}s")

    # Conclusion
    print(f"\n" + "="*100)
    if failed == 0:
        print("🎉 ALL TESTS PASSED! ✅")
    else:
        print(f"⚠️  {failed} test(s) need review")
    print("="*100 + "\n")

    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": 20,
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{passed*5}%"
        },
        "results": results
    }

    with open("test_report_v2.json", 'w') as f:
        json.dump(report, f, indent=2)
    print("📄 Report saved to: test_report_v2.json\n")

if __name__ == "__main__":
    run_tests()
