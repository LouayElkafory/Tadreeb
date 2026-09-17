#!/usr/bin/env python3
"""
Interactive CLI to test Tadreeb AI with conversational memory and RAG retrieval.
Run with:
    ./.venv/bin/python test_interactive_chat.py
"""
import sys
from pathlib import Path

# Add project root and generation folder to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "05_generation"))

from generate_answer import generate_answer

def main():
    print("=" * 60)
    print("🤖 مرحباً بك في تجربة Tadreeb AI مع الذاكرة والـ RAG!")
    print("اكتب سؤالك، أو اكتب 'خروج' أو 'exit' للإنهاء.")
    print("=" * 60 + "\n")

    history = []

    while True:
        try:
            user_input = input("\n👤 أنت: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["خروج", "exit", "quit", "q"]:
                print("\nمع السلامة! 👋")
                break

            print("\n⏳ جاري البحث والتوليد عبر الموديل...")
            result = generate_answer(user_input, history=history)

            print(f"\n🤖 Tadreeb AI:\n{result['answer']}")

            if result.get("sources"):
                print("\n📚 المصادر المسترجعة:")
                for s in result["sources"][:3]:
                    doc = s.get("document", "Doc")
                    page = s.get("page", "")
                    title = s.get("title", doc)
                    print(f"  - [{s.get('org', '').upper()}] {title} (صفحة {page})")

            # Update conversation history
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": result["answer"]})

        except KeyboardInterrupt:
            print("\n\nتم إنهاء المحادثة. مع السلامة! 👋")
            break
        except Exception as e:
            print(f"\n❌ حدث خطأ: {e}")

if __name__ == "__main__":
    main()
