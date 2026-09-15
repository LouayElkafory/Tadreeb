"""
The integration point: question -> RAG retrieval -> grounded prompt -> Qwen -> answer.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "03_rag_pipeline" / "retrieval"))
from retriever import retrieve

from ollama_client import ask_model
from prompt_templates import build_prompt

NO_CONTEXT_MESSAGE = "مش لاقي معلومات كافية في المصادر المتاحة عشان أجاوب على السؤال ده بدقة."
UNAVAILABLE_MESSAGE = "في مشكلة مؤقتة في الاتصال بالنموذج، جرب تاني بعد شوية."


def build_context(chunks: list[dict]) -> str:
    return "\n\n".join(chunk["text"] for chunk in chunks)


def generate_answer(question: str) -> dict:
    """Run the full RAG + Qwen pipeline for one user question."""
    question = question.strip()
    if not question:
        return {"answer": NO_CONTEXT_MESSAGE, "sources": []}

    try:
        chunks = retrieve(question)
    except Exception:
        return {"answer": UNAVAILABLE_MESSAGE, "sources": []}

    if not chunks:
        return {"answer": NO_CONTEXT_MESSAGE, "sources": []}

    prompt = build_prompt(context=build_context(chunks), question=question)

    try:
        answer = ask_model(prompt)
    except Exception:
        return {"answer": UNAVAILABLE_MESSAGE, "sources": []}

    return {"answer": answer, "sources": chunks}
