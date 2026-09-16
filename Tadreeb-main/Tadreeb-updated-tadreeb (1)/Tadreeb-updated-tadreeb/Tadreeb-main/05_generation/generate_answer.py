"""
The integration point: question -> RAG retrieval -> grounded prompt -> Qwen -> answer.
"""
import re
import sys
from pathlib import Path

from langdetect import DetectorFactory, LangDetectException, detect

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "03_rag_pipeline" / "retrieval"))
from retriever import Retriever, VALID_PROGRAM_NAMES

from ollama_client import ask_model
from prompt_templates import build_prompt

DetectorFactory.seed = 0  # langdetect is otherwise non-deterministic for short text.

ARABIC_CHARACTERS = re.compile(r"[\u0600-\u06ff]")
CJK_CHARACTERS = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff]")
ACRONYM = re.compile(r"\b[A-Z][A-Z0-9-]{2,}\b")
MIN_RETRIEVAL_SCORE = 0.72


def retrieval_queries(question: str) -> list[str]:
    """Add focused English retrieval hints for common Egyptian-Arabic questions.

    Most official PDFs are English, while users naturally ask in Egyptian
    Arabic.  These hints improve *search only*; they never add facts to the
    model context or answer.  The original question remains the first query.
    """
    q = question.lower()
    queries = [question]
    if any(word in q for word in ("شرط", "تقديم", "أقدم", "قبول", "eligible")):
        queries.append("eligibility criteria application requirements who may apply")
        if re.search(r"(?<![a-z])iti(?![a-z])", q):
            queries.append(
                "ITI professional training program eligibility Egyptian nationals bachelor's degree "
                "graduated last five academic years full-time commitment"
            )
    if any(word in q for word in ("خريج", "تجارة", "تجاره", "كلية", "كليه", "مناسب")):
        queries.append("ITI eligible tracks all university graduates Faculty of Commerce business graduates")
    if any(word in q for word in ("مجاني", "مجانى", "تكلفة", "تكلفه", "رسوم", "fee", "free")):
        queries.append("government-funded scholarship free training fees")
    if any(word in q for word in ("موعد", "ميعاد", "تاريخ", "deadline", "when apply")):
        queries.append("applications open intake period current dates deadlines")
    return list(dict.fromkeys(queries))


def detect_response_language(question: str) -> str:
    """Return en for a clear English question; otherwise use Egyptian Arabic.

    Arabic-script questions are handled directly because mixed questions such as
    "DEPI ايه شروطها؟" should get an Egyptian-Arabic answer.  langdetect is
    used for Latin-script text, and its uncertain/non-English result falls back
    to Arabic instead of accidentally selecting a third answer language.
    """
    if ARABIC_CHARACTERS.search(question):
        return "ar"
    try:
        return "en" if detect(question) == "en" else "ar"
    except LangDetectException:
        return "ar"


def no_context_message(language: str) -> str:
    return (
        "I couldn't find enough information in the available sources to answer this accurately."
        if language == "en"
        else "مش لاقي معلومات كافية في المصادر المتاحة عشان أجاوب على السؤال ده بدقة."
    )


def unavailable_message(language: str) -> str:
    return (
        "There is a temporary problem connecting to the model. Please try again shortly."
        if language == "en"
        else "في مشكلة مؤقتة في الاتصال بالنموذج، جرب تاني بعد شوية."
    )


def unreliable_answer_message(language: str) -> str:
    return (
        "I couldn't produce a reliable answer from the available sources, so I won't guess."
        if language == "en"
        else "مش قادر أطلع إجابة موثوقة من المصادر المتاحة، فمش هخمن."
    )

# واحدة بس لكل العملية - مش بنفتح اتصال جديد بالـChromaDB مع كل سؤال.
_retriever = Retriever()


def detect_programs(question: str) -> list[str]:
    """
    فلترة بسيطة بالاسم (iti/nti/depi/itida) لو السؤال بيذكرهم صراحة.
    مهمة عشان من غير فلتر، الـsimilarity search بيرجع أحيانًا chunks من
    برنامج تاني خالص (النصوص القصيرة/المشوشة بتظهر قريبة من أي سؤال).
    """
    q = question.lower()
    # Arabic letters are word characters for Python's \b, so "الiti" was not
    # recognized as ITI and the search accidentally mixed in other organizations.
    # Match only against Latin letters instead; this still avoids matching ITI
    # inside an English word such as "utility" and avoids matching it in ITIDA.
    return [
        org
        for org in sorted(VALID_PROGRAM_NAMES, key=len, reverse=True)
        if re.search(rf"(?<![a-z]){re.escape(org)}(?![a-z])", q)
    ]


def build_context(chunks: list[dict]) -> str:
    """Keep source boundaries visible to the model instead of mixing documents."""
    return "\n\n".join(
        f"[SOURCE {index}: {chunk['metadata'].get('document', 'official document')}, "
        f"page {chunk['metadata'].get('page', '?')}]\n{chunk['text']}"
        for index, chunk in enumerate(chunks, start=1)
    )


def retrieve_chunks(question: str) -> list[dict]:
    """
    لو السؤال بيذكر برنامج واحد بس، بنفلتر عليه عشان منجيبش chunks من
    برامج تانية. لو بيذكر أكتر من برنامج (سؤال مقارنة)، بنجيب لكل واحد
    فيهم على حدة عشان الاتنين يبقوا موجودين في الـcontext. من غير ما
    البرامج تتذكر، بنعمل بحث عام من غير فلتر.
    """
    programs = detect_programs(question)
    queries = retrieval_queries(question)

    if len(programs) > 1:
        merged: list[dict] = []
        seen = set()
        for org in programs:
            for query in queries:
                for chunk in _retriever.retrieve(query, program_name=org, top_k=4):
                    if chunk["score"] < MIN_RETRIEVAL_SCORE:
                        continue
                    key = (chunk["metadata"].get("document"), chunk["metadata"].get("page"), chunk["text"])
                    if key not in seen:
                        seen.add(key)
                        merged.append(chunk)
        return sorted(merged, key=lambda chunk: chunk["score"], reverse=True)[:6]

    program = programs[0] if len(programs) == 1 else None
    merged: list[dict] = []
    seen = set()
    for query in queries:
        for chunk in _retriever.retrieve(query, program_name=program, top_k=6):
            if chunk["score"] < MIN_RETRIEVAL_SCORE:
                continue
            key = (chunk["metadata"].get("document"), chunk["metadata"].get("page"))
            if key not in seen:
                seen.add(key)
                merged.append(chunk)
    return sorted(merged, key=lambda chunk: chunk["score"], reverse=True)[:5]


def is_safe_answer(answer: str, language: str, context: str) -> bool:
    """Reject known failure modes before a response reaches the user."""
    if not answer or CJK_CHARACTERS.search(answer):
        return False

    if language == "en":
        # An English answer may keep official abbreviations, but must not turn
        # into Arabic due to the model's Egyptian-Arabic persona.
        if ARABIC_CHARACTERS.search(answer):
            return False
        try:
            if detect(answer) != "en":
                return False
        except LangDetectException:
            return False
    elif not ARABIC_CHARACTERS.search(answer):
        return False

    context_acronyms = {token.upper() for token in ACRONYM.findall(context)}
    answer_acronyms = {token.upper() for token in ACRONYM.findall(answer)}
    # This catches fabricated names such as EPITA in the reported failure.
    if answer_acronyms - context_acronyms:
        return False
    return True


def correction_prompt(prompt: str, language: str) -> str:
    required_language = "English" if language == "en" else "Egyptian Arabic"
    return (
        f"{prompt}\n\nFINAL SAFETY CHECK: Write the answer again using ONLY the retrieved "
        f"context. Output ONLY {required_language}. Do not output Chinese, Japanese, Korean, "
        "or an acronym/name that is absent from the context. If the context cannot support an "
        "answer, state that the information is unavailable in the provided sources."
    )


def generate_answer(question: str) -> dict:
    """Run the full RAG + Qwen pipeline for one user question."""
    question = question.strip()
    language = detect_response_language(question) if question else "ar"
    if not question:
        return {"answer": no_context_message(language), "sources": []}

    try:
        chunks = retrieve_chunks(question)
    except Exception:
        return {"answer": unavailable_message(language), "sources": []}

    if not chunks:
        return {"answer": no_context_message(language), "sources": []}

    context = build_context(chunks)
    prompt = build_prompt(
        context=context,
        question=question,
        response_language=language,
    )

    try:
        answer = ask_model(prompt)
        if not is_safe_answer(answer, language, context):
            answer = ask_model(correction_prompt(prompt, language))
    except Exception:
        return {"answer": unavailable_message(language), "sources": []}

    if not is_safe_answer(answer, language, context):
        return {"answer": unreliable_answer_message(language), "sources": []}

    return {"answer": answer, "sources": chunks}
