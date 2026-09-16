"""
The integration point: question -> RAG retrieval -> grounded prompt -> Qwen -> answer.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "03_rag_pipeline" / "retrieval"))
from retriever import Retriever, VALID_PROGRAM_NAMES

from ollama_client import ask_model
from prompt_templates import build_prompt

NO_CONTEXT_MESSAGE = "مش لاقي معلومات كافية في المصادر المتاحة عشان أجاوب على السؤال ده بدقة."
UNAVAILABLE_MESSAGE = "في مشكلة مؤقتة في الاتصال بالنموذج، جرب تاني بعد شوية."

# واحدة بس لكل العملية - مش بنفتح اتصال جديد بالـChromaDB مع كل سؤال.
_retriever = Retriever()


def detect_programs(question: str) -> list[str]:
    """
    فلترة بسيطة بالاسم (iti/nti/depi/itida) لو السؤال بيذكرهم صراحة.
    مهمة عشان من غير فلتر، الـsimilarity search بيرجع أحيانًا chunks من
    برنامج تاني خالص (النصوص القصيرة/المشوشة بتظهر قريبة من أي سؤال).
    """
    q = question.lower()
    # \b عشان "iti" متطابقش جوه "itida" (substring)
    return [org for org in sorted(VALID_PROGRAM_NAMES) if re.search(rf"\b{org}\b", q)]


def build_context(chunks: list[dict]) -> str:
    return "\n\n".join(chunk["text"] for chunk in chunks)


def retrieve_chunks(question: str) -> list[dict]:
    """
    لو السؤال بيذكر برنامج واحد بس، بنفلتر عليه عشان منجيبش chunks من
    برامج تانية. لو بيذكر أكتر من برنامج (سؤال مقارنة)، بنجيب لكل واحد
    فيهم على حدة عشان الاتنين يبقوا موجودين في الـcontext. من غير ما
    البرامج تتذكر، بنعمل بحث عام من غير فلتر.
    """
    programs = detect_programs(question)

    if len(programs) == 1:
        return _retriever.retrieve(question, program_name=programs[0])

    if len(programs) > 1:
        merged: list[dict] = []
        seen = set()
        for org in programs:
            for chunk in _retriever.retrieve(question, program_name=org, top_k=3):
                key = (chunk["metadata"].get("document"), chunk["metadata"].get("page"))
                if key not in seen:
                    seen.add(key)
                    merged.append(chunk)
        return merged

    return _retriever.retrieve(question)


def generate_answer(question: str) -> dict:
    """Run the full RAG + Qwen pipeline for one user question."""
    question = question.strip()
    if not question:
        return {"answer": NO_CONTEXT_MESSAGE, "sources": []}

    try:
        chunks = retrieve_chunks(question)
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
