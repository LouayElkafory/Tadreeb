"""
Test Runner for Tadreeb Faiss RAG API - Execute 20 Test Cases
"""
import requests
import json
from typing import Dict, List
from datetime import datetime

API_URL = "http://localhost:8001/api/chat"

class TestRunner:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def run_test(self, test_case: Dict) -> Dict:
        """Execute a single test case."""
        test_id = test_case["test_id"]

        try:
            # Send request
            response = requests.post(
                API_URL,
                json=test_case["request"],
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            # Validate response
            expected = test_case["expected"]

            # Check 1: Chunk count
            chunk_count_ok = data.get("chunk_count") == expected["chunk_count"]

            # Check 2: Keywords in answer
            answer = data.get("answer", "").lower()
            keywords_ok = all(
                kw.lower() in answer
                for kw in expected["contains_keywords"]
            )

            # Check 3: Average score
            avg_score_ok = data.get("avg_score", 0) >= expected["min_avg_score"]

            # Check 4: Sources present
            sources_ok = len(data.get("sources", [])) > 0 == expected["should_have_sources"]

            # Determine pass/fail
            passed = chunk_count_ok and avg_score_ok and sources_ok

            result = {
                "test_id": test_id,
                "category": test_case["category"],
                "language": test_case["language"],
                "status": "✅ PASS" if passed else "❌ FAIL",
                "passed": passed,
                "message": test_case["request"]["message"][:50],
                "checks": {
                    "chunk_count": f"{data.get('chunk_count')}/3 ✓" if chunk_count_ok else f"{data.get('chunk_count')}/3 ✗",
                    "keywords": "✓" if keywords_ok else "✗",
                    "avg_score": f"{data.get('avg_score', 0):.6f} ✓" if avg_score_ok else f"{data.get('avg_score', 0):.6f} ✗",
                    "sources": "✓" if sources_ok else "✗"
                },
                "response_time": response.elapsed.total_seconds(),
                "sample_source": data["sources"][0]["metadata"] if data.get("sources") else None
            }

            if passed:
                self.passed += 1
            else:
                self.failed += 1

            return result

        except requests.exceptions.RequestException as e:
            self.failed += 1
            return {
                "test_id": test_id,
                "category": test_case["category"],
                "language": test_case["language"],
                "status": "❌ ERROR",
                "passed": False,
                "error": str(e),
                "message": test_case["request"]["message"][:50]
            }

    def run_all_tests(self, test_cases: List[Dict]):
        """Run all test cases."""
        print("\n" + "="*90)
        print("🧪 TADREEB FAISS RAG API - 20 TEST CASES")
        print("="*90 + "\n")

        for i, test_case in enumerate(test_cases, 1):
            result = self.run_test(test_case)
            self.results.append(result)

            # Print inline result
            status = result["status"]
            category = result["category"].ljust(25)
            language = result["language"].ljust(8)
            message = result["message"][:35].ljust(35)

            print(f"Test {i:2d} | {status} | {category} | {language} | {message}")

            if "checks" in result:
                checks = result["checks"]
                print(f"         └─ Chunks: {checks['chunk_count']:<8} | "
                      f"Score: {checks['avg_score']:<12} | "
                      f"Keywords: {checks['keywords']:<3} | "
                      f"Sources: {checks['sources']:<3}")
            elif "error" in result:
                print(f"         └─ Error: {result['error'][:60]}")
            print()

    def print_summary(self):
        """Print test summary."""
        total = len(self.results)

        print("\n" + "="*90)
        print("📊 TEST SUMMARY")
        print("="*90)

        print(f"\n✅ PASSED: {self.passed}/{total} ({self.passed*100//total}%)")
        print(f"❌ FAILED: {self.failed}/{total} ({self.failed*100//total}%)")

        # Group by category
        print(f"\n📂 BY CATEGORY:")
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0}
            categories[cat]["total"] += 1
            if result["passed"]:
                categories[cat]["passed"] += 1

        for cat, stats in sorted(categories.items()):
            pct = stats["passed"] * 100 // stats["total"]
            status = "✅" if stats["passed"] == stats["total"] else "⚠️"
            print(f"   {status} {cat:<30} {stats['passed']}/{stats['total']} ({pct}%)")

        # By language
        print(f"\n🌐 BY LANGUAGE:")
        languages = {}
        for result in self.results:
            lang = result["language"]
            if lang not in languages:
                languages[lang] = {"total": 0, "passed": 0}
            languages[lang]["total"] += 1
            if result["passed"]:
                languages[lang]["passed"] += 1

        for lang, stats in sorted(languages.items()):
            pct = stats["passed"] * 100 // stats["total"]
            status = "✅" if stats["passed"] == stats["total"] else "⚠️"
            print(f"   {status} {lang:<20} {stats['passed']}/{stats['total']} ({pct}%)")

        # Performance
        print(f"\n⏱️  PERFORMANCE:")
        valid_times = [r["response_time"] for r in self.results if "response_time" in r]
        if valid_times:
            avg_time = sum(valid_times) / len(valid_times)
            min_time = min(valid_times)
            max_time = max(valid_times)
            print(f"   Average response time: {avg_time:.3f}s")
            print(f"   Min response time: {min_time:.3f}s")
            print(f"   Max response time: {max_time:.3f}s")

        # Conclusion
        print(f"\n" + "="*90)
        if self.failed == 0:
            print("🎉 ALL TESTS PASSED! ✅")
        else:
            print(f"⚠️  {self.failed} test(s) failed. Please review the results above.")
        print("="*90 + "\n")

    def save_report(self, filename: str = "test_report.json"):
        """Save detailed test report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.results),
                "passed": self.passed,
                "failed": self.failed,
                "pass_rate": f"{self.passed*100//len(self.results)}%"
            },
            "results": self.results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📄 Report saved to: {filename}")


def main():
    """Main execution."""
    # Load test cases
    with open("test_cases_20.json", 'r', encoding='utf-8') as f:
        test_data = json.load(f)

    test_cases = test_data["test_cases"]

    # Run tests
    runner = TestRunner()
    runner.run_all_tests(test_cases)
    runner.print_summary()
    runner.save_report()


if __name__ == "__main__":
    main()
