"""
The integration point: question + history -> RAG retrieval -> grounded prompt with memory -> Qwen -> answer.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "03_rag_pipeline" / "retrieval"))
from retriever import retrieve

from ollama_client import ask_model
from prompt_templates import build_memory_prompt, build_prompt

NO_CONTEXT_MESSAGE = "مش لاقي معلومات كافية في المصادر المتاحة عشان أجاوب على السؤال ده بدقة."
UNAVAILABLE_MESSAGE = "في مشكلة مؤقتة في الاتصال بالنموذج، جرب تاني بعد شوية."


def build_context(chunks: list[dict]) -> str:
    return "\n\n".join(chunk["text"] for chunk in chunks)


def contextualize_query(question: str, history: list[dict] | None) -> str:
    """If the question is a pronoun/follow-up, blend context from recent user messages."""
    if not history:
        return question

    q_lower = question.lower()
    # Check if question contains pronouns / follow-up references
    is_followup = any(
        kw in q_lower
        for kw in ["فيها", "عنها", "شروطها", "مدتها", "البرنامج ده", "المسار ده", "المؤسسة دي", "it", "them", "there"]
    ) or len(question.split()) <= 3

    if is_followup:
        # Find the most recent user turn that mentioned specific topics
        for turn in reversed(history):
            if turn.get("role") == "user":
                prev_text = turn.get("content", "")
                return f"{prev_text} - {question}"

    return question


def is_memory_meta_question(question: str) -> bool:
    """Check if the user is explicitly asking about what was said in the conversation."""
    q_norm = question.strip().lower()
    meta_patterns = [
        "أول سؤال",
        "اول سؤال",
        "سألتك عن إيه",
        "سالتك عن ايه",
        "سألتك في إيه",
        "سالتك في ايه",
        "فكرني",
        "قلتلك إيه",
        "قولتلك ايه",
        "سؤالي السابق",
        "السؤال اللي فات",
        "what was my first question",
        "what did i ask",
        "remind me",
    ]
    return any(p in q_norm for p in meta_patterns)


def generate_answer(question: str, history: list[dict] | None = None) -> dict:
    """Run the full RAG + LLM pipeline with multi-turn conversation memory."""
    question = question.strip()
    if not question:
        return {"answer": NO_CONTEXT_MESSAGE, "sources": []}

    # Handle direct memory inquiries (e.g. "أنا سألتك في أول سؤال عن إيه؟")
    if is_memory_meta_question(question) and history:
        user_messages = [t["content"] for t in history if t.get("role") == "user"]
        if user_messages:
            prompt = build_memory_prompt(question=question, history=history)
            try:
                answer = ask_model(prompt)
                return {"answer": answer, "sources": []}
            except Exception:
                first_q = user_messages[0]
                return {
                    "answer": f"أول سؤال سألتهولي كان: **\"{first_q}\"**",
                    "sources": [],
                }

    # Contextualize query for RAG retrieval
    search_query = contextualize_query(question, history)

    try:
        chunks = retrieve(search_query)
    except Exception:
        chunks = []

    # If contextual query yielded no chunks, try raw question
    if not chunks and search_query != question:
        try:
            chunks = retrieve(question)
        except Exception:
            chunks = []

    # If still no chunks and history is empty
    if not chunks and not history:
        return {"answer": NO_CONTEXT_MESSAGE, "sources": []}

    prompt = build_prompt(context=build_context(chunks), question=question, history=history)

    try:
        answer = ask_model(prompt)
    except Exception:
        return {"answer": UNAVAILABLE_MESSAGE, "sources": []}

    return {"answer": answer, "sources": chunks}
