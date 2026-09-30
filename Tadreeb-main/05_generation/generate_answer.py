"""
The integration point: question + history -> RAG retrieval -> grounded prompt -> LLM -> answer.

The rule this module enforces is that an answer is only produced when retrieval
found something. Previously, an empty retrieval result still reached the model as
long as the conversation had any history at all, which meant the model answered
from its own knowledge with no sources - the main source of made-up hours,
dates and admission rules. Now an empty result is reported as "not in the
sources", which is the honest answer.
"""
import os
import re
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "03_rag_pipeline" / "retrieval"))
from organizations import detect_organizations
from query_understanding import analyze, detect_language, foreign_track_names
from retriever import retrieve

from ollama_client import ask_model
from prompt_templates import build_memory_prompt, build_prompt

NO_CONTEXT_MESSAGES = {
    "ar": (
        "مش لاقي معلومات موثوقة كفاية في المصادر المتاحة عشان أجاوب على السؤال ده بدقة. "
        "جرب تسأل عن ITI أو NTI أو DEPI أو ITIDA بشكل أوضح."
    ),
    "en": (
        "I could not find reliable enough information in the available sources to answer "
        "this accurately. Please ask more specifically about ITI, NTI, DEPI, or ITIDA."
    ),
}
# Distinct from NO_CONTEXT_MESSAGE: retrieval DID find the right sources here -
# this fires only when the model, even after retries, kept naming an
# organisation those sources never mention (confirmed reproducible: asked for
# ITI's tracks against sources verified to be 100% ITI-only, it named DEPI/
# ITIDA in 3 of 3 attempts, surviving two retries each time). Serving that
# answer anyway would mix a real, sourced fact with a fabricated one in a way
# the user has no way to tell apart - worse than refusing.
ORG_CONFUSION_MESSAGES = {
    "ar": (
        "المصادر بتاعتنا فيها إجابة على السؤال ده، بس حصل لبس واتخلطت معلومات جهة "
        "تانية مش موجودة في المصادر دي. جرب تسأل تاني أو بصيغة مختلفة."
    ),
    "en": (
        "The sources contain an answer, but the generated response mixed in an organisation "
        "that is not present in those sources. Please try again with different wording."
    ),
}

# Arabic and mixed Arabic/English questions are matched against a mostly-English
# corpus. The rule-based layer in query_understanding handles that for free on
# every request - it reads the intent, the organisation and any named track, and
# appends the English terms the documents use.
#
# This is the last resort when that still found nothing: ONE LLM call that
# rewrites the question into a clean English retrieval query, on a request that
# would otherwise be refused. It never runs on a request that already succeeded,
# which is why the common path costs no extra call.
#
#   auto (default)  rewrite only after a failed first retrieval
#   always          rewrite up front, but only when the rules found no anchor
#   off             never rewrite
QUERY_REWRITE = os.getenv("QUERY_REWRITE", os.getenv("QUERY_TRANSLATION", "auto")).strip().lower()
REWRITE_ENABLED = QUERY_REWRITE != "off"
UNAVAILABLE_MESSAGES = {
    "ar": "في مشكلة مؤقتة في الاتصال بالنموذج، جرب تاني بعد شوية.",
    "en": "There is a temporary connection problem with the model. Please try again shortly.",
}

# Pronouns and particles that only make sense against an earlier turn. These are
# matched as whole words: "ده" as a substring also sits inside "عنده" and "بعده",
# which would flag perfectly self-contained questions as follow-ups.
_FOLLOWUP_WORDS = (
    "فيها", "عنها", "عنه", "شروطها", "مدتها", "مدته",
    "ده", "دي", "دول", "ليها", "بتاعها", "بتاعه", "ليهم",
    "it", "them", "there", "those", "these",
)
_FOLLOWUP_PHRASES = ("طب و", "what about", "وايه كمان", "وإيه كمان")
_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)  # letters only, any script
_FOLLOWUP_PATTERN = re.compile(
    r"(?<![^\W\d_])(?:" + "|".join(re.escape(w) for w in _FOLLOWUP_WORDS) + r")(?![^\W\d_])",
    re.UNICODE,
)


def is_followup(question: str) -> bool:
    """Whether a question leans on the previous turn to be understood.

    The old test treated any question of three words or fewer as a follow-up.
    Arabic questions are routinely that short - "ايه هو DEPI؟" is three words - so
    most first questions were silently glued to an unrelated earlier turn, which
    dragged retrieval off topic. Now only an explicit back-reference counts, or a
    fragment too short to carry a topic of its own.
    """
    normalized = question.strip().lower()
    if _FOLLOWUP_PATTERN.search(normalized):
        return True
    if any(phrase in normalized for phrase in _FOLLOWUP_PHRASES):
        return True
    # A bare fragment too short to carry a topic of its own, e.g. "والشروط؟"
    words = [w for w in _WORD.findall(question) if len(w) > 1]
    return len(words) <= 2


def contextualize_query(question: str, history: list[dict] | None) -> str:
    """Blend in the previous user turn when the question is a back-reference."""
    if not history or not is_followup(question):
        return question
    for turn in reversed(history):
        if turn.get("role") == "user" and turn.get("content", "").strip():
            return f"{turn['content'].strip()} - {question}"
    return question


def _relevant_history(history: list[dict] | None, allowed_orgs: set[str]) -> list[dict] | None:
    """Drop earlier turns that named a DIFFERENT organisation than this answer's
    sources belong to.

    The model is shown conversation history to sound natural across turns, not
    to answer from - but it does not reliably keep the two apart: shown an
    earlier ITI turn, asked next for NTI's tracks (retrieval correctly scoped to
    NTI-only sources), it produced ITI's real track names anyway, never naming
    "ITI" so the org-name guard alone did not catch it (see `_foreign_content`,
    which does). That guard stops the wrong answer from reaching the user, but
    it does so by refusing - this removes the temptation at its source instead,
    so switching organisations mid-conversation gets a real answer, not a
    refusal. A turn naming no organisation (or the same one) is always kept -
    this only removes turns that are unambiguously about something else.
    """
    if not history or not allowed_orgs:
        return history

    # Turns are dropped in (user, assistant) pairs, keyed by the org the USER's
    # question named - not the assistant's answer. Confirmed necessary: the
    # contaminating answer above ("2D Animation and Motion Graphics, Data
    # Management, ...") names no organisation at all, only real ITI track
    # titles, so checking the assistant's own text finds nothing to drop.
    kept: list[dict] = []
    i = 0
    while i < len(history):
        turn = history[i]
        if turn.get("role") != "user":
            kept.append(turn)
            i += 1
            continue
        mentioned = detect_organizations(turn.get("content") or "")
        pair = [turn]
        if i + 1 < len(history) and history[i + 1].get("role") != "user":
            pair.append(history[i + 1])
            i += 1
        if not mentioned or mentioned & allowed_orgs:
            kept.extend(pair)
        i += 1
    return kept


def is_memory_meta_question(question: str) -> bool:
    """Check if the user is explicitly asking about what was said in the conversation."""
    q_norm = question.strip().lower()
    meta_patterns = [
        "أول سؤال", "اول سؤال",
        "سألتك عن إيه", "سالتك عن ايه",
        "سألتك في إيه", "سالتك في ايه",
        "فكرني", "قلتلك إيه", "قولتلك ايه",
        "سؤالي السابق", "السؤال اللي فات",
        "what was my first question", "what did i ask", "remind me",
    ]
    return any(p in q_norm for p in meta_patterns)


# The model (base or fine-tuned - confirmed on both) intermittently emits CJK
# characters mid-answer despite the prompt forbidding it, and separately,
# sometimes names an organisation that is not in the retrieved sources at all -
# confirmed by direct testing: asked for ITI's tracks, with retrieved context
# verified to mention only ITI, it named DEPI and ITIDA anyway. Neither failure
# is reliably prevented by prompt wording alone (tested removing the system
# prompt's own org list; the mis-naming persisted), so both are caught by
# checking the actual output, the same way the CJK check already did, rather
# than trusting the model to have followed the prompt.
# Any script that has no business in an Arabic/English answer. Started as CJK
# only; the model was then seen answering NTI's summer-training question with
# "30ساعة навыки мягкие + 90ساعة навыки технические" - Russian slipped straight
# past a CJK-only check to the user. Covers Greek, Cyrillic, Hebrew, Devanagari,
# Thai, CJK (incl. kana) and Hangul.
_CJK = re.compile(
    r"[\u0370-\u03ff\u0400-\u04ff\u0590-\u05ff\u0900-\u097f\u0e00-\u0e7f"
    r"\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uf900-\ufaff]"
)
_ARABIC_OUTPUT = re.compile(r"[\u0621-\u064a]")
# A run of consecutive English words, uninterrupted by Arabic text.
_LATIN_RUN = re.compile(r"[A-Za-z][\w&/.,'()+\-]*(?:[ \t]+[A-Za-z0-9][\w&/.,'()+\-]*)*")
# Words that build an English *sentence* but essentially never appear inside a
# programme or job-profile name. Deliberately excludes and/or/for/with/in/of/
# the: real names are full of those ("Vulnerability Analyst and Penetration
# Tester", "Applied AI Agents for Education and Teaching Professional"), and
# counting them rejected every correct Arabic answer that listed DEPI's tracks.
_SENTENCE_WORDS = {
    "is", "are", "was", "were", "be", "been", "this", "these", "those", "that",
    "it", "they", "you", "we", "offers", "offer", "provides", "provide",
    "designed", "can", "will", "has", "have", "includes", "which", "there",
}
_MIN_SENTENCE_RUN = 5

GENERATION_GUARD_MESSAGES = {
    "ar": "حصلت مشكلة مؤقتة في صياغة الإجابة. جرب تسأل تاني بعد شوية.",
    "en": "There was a temporary problem formatting the answer. Please try again shortly.",
}


def _foreign_orgs(answer: str, allowed_orgs: set[str]) -> set[str]:
    """Organisations the answer names that are not among the retrieved sources.

    A comparison question legitimately retrieves and discusses several
    organisations - `allowed_orgs` is exactly the set the sources actually
    belong to, so this only flags a name that should not be there at all, never
    penalises a correct multi-organisation answer.
    """
    if not allowed_orgs:
        return set()
    return detect_organizations(answer) - allowed_orgs


def _foreign_content(answer: str, allowed_orgs: set[str]) -> set[str]:
    """Everything about `answer` that has no business being there given
    `allowed_orgs`: another organisation's name, or - the harder case,
    confirmed happening with conversation history in play - another
    organisation's real track/programme/job-profile names, stated without ever
    naming that organisation. Asked for NTI's tracks with a conversation history
    that held an earlier ITI answer, the model produced a track list correctly
    scoped to NTI's *sources* but silently padded with ITI's actual track names
    from its own previous turn - `_foreign_orgs` alone missed this because "ITI"
    was never written down; `foreign_track_names` catches the track names.
    """
    return _foreign_orgs(answer, allowed_orgs) | foreign_track_names(answer, allowed_orgs)


def _matches_output_language(text: str, language: str) -> bool:
    """Keep a wrong-language answer out of the UI even when the model ignores a prompt."""
    has_arabic = bool(_ARABIC_OUTPUT.search(text))
    if language == "en":
        return not has_arabic
    # Track and job-profile names are English and belong in an Egyptian Arabic
    # answer. Drift is a run of English long enough to be a sentence AND built
    # with sentence words ("The institute offers tracks that are designed...").
    # Arabic text is NOT required: asked for ITI's tracks, the model often
    # answers with nothing but the ten track names - correct, sourced, and
    # language-neutral. Requiring Arabic rejected that answer on all three
    # attempts and showed the user an error instead.
    return not _has_english_sentence(text)


def _has_english_sentence(text: str) -> bool:
    for run in _LATIN_RUN.findall(text):
        words = [w.strip(".,()'").lower() for w in run.split()]
        if len(words) >= _MIN_SENTENCE_RUN and _SENTENCE_WORDS.intersection(words):
            return True
    return False


def _generate_clean(
    prompt: str,
    retries: int = 1,
    allowed_orgs: set[str] | None = None,
    language: str = "ar",
) -> str:
    """Ask the model and only accept an answer in the intended language.

    Prompting reduces Chinese text and language drift; this validator guarantees
    that a repeated bad generation is never returned to the user.
    """
    allowed_orgs = allowed_orgs or set()

    def _is_clean(text: str) -> bool:
        return (
            not _CJK.search(text)
            and not _foreign_content(text, allowed_orgs)
            and _matches_output_language(text, language)
        )

    def _problem_count(text: str) -> int:
        return (
            len(_CJK.findall(text))
            + len(_foreign_content(text, allowed_orgs))
            + (0 if _matches_output_language(text, language) else 1)
        )

    answer = ask_model(prompt)
    for _ in range(retries):
        if _is_clean(answer):
            return answer
        foreign = _foreign_content(answer, allowed_orgs)
        if _CJK.search(answer):
            reason = "foreign-script characters (e.g. Chinese/Russian)"
        elif foreign:
            reason = f"content not in the sources: {foreign}"
        else:
            reason = f"wrong output language (expected {language})"
        print(f"Warning: model output problem ({reason}); retrying once.", flush=True)
        retry = ask_model(prompt)
        # Prefer whichever attempt is actually clean; otherwise keep the one
        # with fewer problems rather than trusting the retry blindly.
        if _is_clean(retry) or _problem_count(retry) < _problem_count(answer):
            answer = retry
    return answer


def _answer_memory_question(question: str, history: list[dict]) -> dict:
    user_messages = [t["content"] for t in history if t.get("role") == "user"]
    language = detect_language(question)
    try:
        return {
            "answer": _generate_clean(
                build_memory_prompt(question, history, language=language),
                language=language,
            ),
            "sources": [],
        }
    except Exception:
        first = user_messages[0] if user_messages else ""
        if language == "en":
            return {"answer": f'Your first question was: **"{first}"**', "sources": []}
        return {"answer": f"أول سؤال سألتهولي كان: **\"{first}\"**", "sources": []}


def generate_answer(
    question: str,
    history: list[dict] | None = None,
    language: str | None = None,
) -> dict:
    """Run the full RAG + LLM pipeline with multi-turn conversation memory.

    `language` ("ar"/"en") is the caller's preference; the question's own
    language takes precedence when it is unambiguous.
    """
    question = (question or "").strip()
    if not question:
        return {"answer": NO_CONTEXT_MESSAGES["ar"], "sources": []}

    # Questions about the conversation itself are answered from history, not the corpus.
    if is_memory_meta_question(question) and history:
        return _answer_memory_question(question, history)

    search_query = contextualize_query(question, history)
    # Language, intent (overview / comparison / duration / training_type /
    # eligibility / application / tracks / specific), the organisation, any named
    # track or program, and the expanded search terms - all rule-based, no LLM.
    plan = analyze(search_query)

    if REWRITE_ENABLED and QUERY_REWRITE == "always" and plan.get("needs_rewrite"):
        rewritten = _rewrite_for_retrieval(search_query)
        if rewritten:
            plan = _merge_plan(plan, analyze(rewritten))

    chunks = _retrieve_safely(plan["search_query"], plan)
    if not chunks and plan["search_query"] != question:
        chunks = _retrieve_safely(question)
    if not chunks and REWRITE_ENABLED:
        rewritten = _rewrite_for_retrieval(question)
        if rewritten:
            chunks = _retrieve_safely(rewritten, _merge_plan(plan, analyze(rewritten)))

    # No sources means no answer. Answering anyway - which is what happened
    # whenever the conversation had history - is exactly how the model ended up
    # inventing programme details.
    if not chunks:
        return {"answer": NO_CONTEXT_MESSAGES[plan["language"]], "sources": []}

    # The organisations the retrieved chunks actually belong to - anything the
    # answer names outside this set has no source behind it at all.
    allowed_orgs = {str(c.get("org", "")).lower() for c in chunks if c.get("org")}
    prompt = build_prompt(
        chunks=chunks,
        question=question,
        history=_relevant_history(history, allowed_orgs),
        language=plan["language"],
        intent=plan["intent"],
    )
    try:
        # Two retries, not one: a single retry on the org-mismatch case (new,
        # confirmed harder to shake than the CJK case) sometimes still left one
        # foreign organisation in - this only adds latency on the already-rare
        # path where the first attempt already failed the check.
        answer = _generate_clean(
            prompt,
            retries=2,
            allowed_orgs=allowed_orgs,
            language=plan["language"],
        )
    except Exception:
        return {"answer": UNAVAILABLE_MESSAGES[plan["language"]], "sources": []}

    if not answer.strip():
        return {"answer": NO_CONTEXT_MESSAGES[plan["language"]], "sources": []}

    if _CJK.search(answer) or not _matches_output_language(answer, plan["language"]):
        return {"answer": GENERATION_GUARD_MESSAGES[plan["language"]], "sources": chunks}

    if _foreign_content(answer, allowed_orgs):
        return {"answer": ORG_CONFUSION_MESSAGES[plan["language"]], "sources": []}

    return {"answer": answer, "sources": chunks}


def _retrieve_safely(query: str, plan: dict | None = None) -> list[dict]:
    try:
        return retrieve(query, plan=plan)
    except Exception as e:
        print(f"Retrieval failed: {e}")
        return []


REWRITE_PROMPT = (
    "Rewrite this user question as a single clear English search query for a "
    "knowledge base about Egyptian technology training programmes (ITI, NTI, "
    "DEPI, ITIDA). The question may be in Arabic, Egyptian Arabic, English, or a "
    "mix of Arabic and English.\n"
    "Rules:\n"
    "- Keep organisation, programme, track and technology names exactly as "
    "written (ITI, DEPI, Data Science, DevOps).\n"
    "- Preserve the meaning. Do not answer the question and do not add facts.\n"
    "- If it is already clear English, repeat it unchanged.\n"
    "- Reply with the query only, on one line.\n\n"
    "Question: {question}\nEnglish query:"
)


@lru_cache(maxsize=256)
def _rewrite_for_retrieval(question: str) -> str:
    """One LLM call turning any question into a clean English retrieval query.

    Rewriting, not translating: the goal is a query that means what the user
    meant, in the language the documents are written in. An English question comes
    back unchanged. Cached, so a repeated question costs one call in total.

    Uses QUERY_LLM_PROVIDER when one is configured (see ollama_client.py), which
    is what lets a fast hosted model do this while the grounded answer is still
    written locally. Failure is not an error - the caller keeps its empty result
    and refuses honestly rather than answering unsourced.
    """
    try:
        rewritten = ask_model(REWRITE_PROMPT.format(question=question), purpose="query").strip()
    except Exception as e:
        print(f"Query rewrite failed: {e}")
        return ""
    # A chatty model sometimes prefixes "Sure, here is..."; keep the last line.
    rewritten = rewritten.splitlines()[-1].strip().strip('"') if rewritten else ""
    return rewritten if 0 < len(rewritten) <= 300 else ""


def _merge_plan(original: dict, rewritten: dict) -> dict:
    """The rewritten question's search terms, with the original's answer language.

    The reply must stay in the language the user wrote in, so `language` and the
    question the prompt shows the model always come from the original. Anything
    the rewrite newly identified - an organisation, a track - is taken from it.
    """
    merged = dict(rewritten)
    merged["question"] = original["question"]
    merged["language"] = original["language"]
    merged["organizations"] = original["organizations"] or rewritten["organizations"]
    for field in ("track", "program", "specialization"):
        merged[field] = original.get(field) or rewritten.get(field, "")
    return merged
