"""
A light query-normalisation layer that runs before retrieval.

    User Question -> Detect Language -> Normalise -> Expand/Translate terms
                  -> Query Embedding -> Vector Search

The corpus is mostly English (official PDFs and web pages) while users ask in
Egyptian Arabic, and two kinds of question were failing for different reasons:

* Broad questions - "عاوز أعرف تفاصيل عن ITI" - carry almost no terms that exist
  in the corpus, so the relevance gate refused them, and when they did get
  through they returned five near-identical chunks about whichever detail
  happened to match. They need more results, drawn from different pages.
* Specific questions - "مدة برامج DEPI قد إيه؟" - name the thing they want in
  Arabic ("مدة") while the corpus says it in English ("duration", "months").

Both are handled here with a rule table rather than a model: an intent is read
off the question, and the English terms for that intent (plus a small Arabic ->
English glossary) are appended to the search query. It costs nothing at runtime
and needs no extra LLM call. `05_generation/generate_answer.py` falls back to a
single Qwen translation call only when this returns no results at all.

Expansion only happens when the question names one of the four organisations.
That is deliberate: appending known-in-corpus English terms raises the retriever's
vocabulary-coverage score, so doing it unconditionally would let genuinely
out-of-corpus questions ("إزاي أطبخ كشري؟") sneak past the refusal gate.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

try:
    from langdetect import DetectorFactory, LangDetectException, detect as detect_langdetect
    # langdetect is otherwise non-deterministic for short questions.
    DetectorFactory.seed = 0
except ImportError:  # Keeps retrieval usable until requirements are installed.
    DetectorFactory = None
    LangDetectException = Exception
    detect_langdetect = None

from organizations import detect_organizations
from text_normalize import tokenize

_ARABIC = re.compile("[ء-ي]")
_LATIN = re.compile("[A-Za-z]")

# How many chunks each kind of question should retrieve. A broad question needs
# to see several parts of the programme material to be answerable at all.
TOP_K_BY_INTENT = {
    "overview": 8,
    "comparison": 8,
    "tracks": 6,
}
DEFAULT_TOP_K = 5

# Which chunk categories answer which kind of question. `structure.py` tags every
# chunk with its categories; retrieval prefers the ones listed here, so
# "مدة تراك Data Science في ITI" prioritises org=ITI + category=duration rather
# than whichever ITI text happens to word-match. A broad question deliberately
# asks for several categories at once, which is what makes an overview an
# overview instead of one fact repeated.
INTENT_CATEGORIES: dict[str, tuple[str, ...]] = {
    "overview": ("organization_info", "programs", "tracks", "duration",
                 "training_type", "eligibility", "application"),
    "comparison": ("organization_info", "programs", "tracks", "duration",
                   "eligibility"),
    "duration": ("duration",),
    "training_type": ("training_type",),
    "eligibility": ("eligibility",),
    "application": ("application", "eligibility"),
    "tracks": ("tracks", "programs"),
    "specific": (),
}

# Chunks from a single page that a broad answer may use, so an overview is not
# eight fragments of the same paragraph. 0 = no limit. Only the broad intents
# cap: on a specific question the best page's chunks are the answer, and
# spreading them out measurably costs ranking quality.
MAX_CHUNKS_PER_SOURCE = {
    "overview": 2,
    "comparison": 2,
}

# For a broad question, how many of the retrieved chunks may share one category.
# Without this an "overview" comes back as eight duration chunks, because the
# duration wording matches strongly and crowds everything else out.
MAX_CHUNKS_PER_CATEGORY = {
    "overview": 2,
    "comparison": 3,
}

# Intents whose questions get the English term expansion below. Broad questions
# need it - they carry almost no corpus vocabulary of their own. Specific ones
# do not: they already name the thing they want, and padding the query with
# generic programme terms measurably *lowers* their ranking (MRR 0.75 -> 0.63 on
# 07_evaluation/test_questions.jsonl). Re-run that evaluation before widening it.
EXPAND_INTENTS = {"overview", "comparison"}

# Where the known program/track/specialisation names come from. Built by
# 03_rag_pipeline/preprocessing/build_knowledge_base.py; a missing file just means
# no name matching, never an error.
KNOWLEDGE_FOLDER = (
    Path(__file__).resolve().parents[2] / "02_data" / "05_structured"
)


def normalize(text: str) -> str:
    """The question reduced to space-separated canonical terms, padded with a
    space at each end.

    This is the same folding + light stemming the lexical retriever uses, so a
    marker written as "مدة" also matches "المدة" and "مدتها". The padding is what
    makes a plain substring test behave as a whole-term test: without it
    "معهد تكنولوجيا المعلومات عنده كام تراك؟" contains "معلومات عن" (inside
    "المعلومات عنده") and was read as a request for general information.
    """
    return " " + " ".join(tokenize(text, drop_stopwords=False)) + " "


def _folded(*phrases: str) -> tuple[str, ...]:
    """Normalise marker phrases once, at import."""
    return tuple(normalize(phrase) for phrase in phrases)


def _matches(markers: tuple[str, ...], normalized: str) -> bool:
    return any(marker in normalized for marker in markers)


# Checked in order: the first intent whose markers appear wins. Comparison and
# the unambiguous overview phrases come first, because those questions often
# also contain a "برامج" or "مدة" that would otherwise capture them.
#
# "ايه هي" / "what is" are deliberately NOT here: they open a specific question
# just as often as a broad one ("إيه هي التراكات المتاحة في DEPI؟" is a question
# about tracks, not an overview request). They are checked last instead, in
# WEAK_OVERVIEW_MARKERS, once every specific intent has had its turn.
INTENT_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("comparison", _folded(
        "الفرق بين", "فرق بين", "مقارنة بين", "ايه احسن", "ولا ايه الافضل",
        "difference between", "compare", "comparison", " vs ", "versus", "better than",
    )),
    ("overview", _folded(
        "تفاصيل عن", "معلومات عن", "عبارة عن", "احكيلي", "عرفني", "نبذة",
        "بيقدم ايه", "بتقدم ايه", "بيعمل ايه", "بتعمل ايه", "بيقدموا ايه",
        "اعرف اكتر", "قولي عن", "كلمني عن", "هي ايه", "هو ايه",
        "tell me about", "overview", "information about", "details about",
        "general information", "who are",
    )),
    ("duration", _folded(
        "مدة", "مدته", "مدتها", "قد ايه", "كام شهر", "كام ساعة", "كام اسبوع",
        "كام يوم", "بتستمر", "فترة التدريب", "بياخد قد",
        "duration", "how long", "how many months", "how many hours", "length of",
    )),
    ("training_type", _folded(
        "اونلاين", "أونلاين", "اون لاين", "حضوري", "عن بعد", "من البيت", "اونلاين ولا",
        "نوع التدريب", "التدريب اونلاين", "هجين", "مدمج", "وجاهي",
        "online or onsite", "online or in-person", "delivery mode", "training type",
        "is it online", "remote or", "hybrid", "blended", "in person",
    )),
    ("application", _folded(
        "ازاي اقدم", "ازاي اسجل", "طريقة التقديم", "خطوات التقديم", "لينك التقديم",
        "الاوراق المطلوبة", "موعد التقديم", "ميعاد التقديم",
        "how do i apply", "how to apply", "application link", "application steps",
        "required documents", "application deadline", "where to apply",
    )),
    ("eligibility", _folded(
        "شروط", "الشروط", "متطلبات", "مؤهل", "ينفع اقدم", "مين يقدر يقدم",
        "قواعد القبول", "القبول", "الفئة المستهدفة",
        "eligibility", "eligible", "requirements", "target audience",
        "who can apply", "admission", "prerequisite", "criteria",
    )),
    ("tracks", _folded(
        "تراك", "تراكات", "مسار", "مسارات", "تخصص", "تخصصات", "برنامج", "برامج",
        "دبلومة", "كورسات", "مجالات",
        "track", "tracks", "program", "programs", "programme", "specialization",
        "specialisation", "diploma", "courses", "fields",
    )),
)

# "DEPI عبارة عن إيه؟" and "NTI بيقدم إيه؟" are overviews; so is a bare "ايه هو
# ITI؟". These only apply when nothing more specific matched.
WEAK_OVERVIEW_MARKERS = _folded(
    "ايه هو", "ايه هي", "يعني ايه", "what is", "what are", "who is",
)

# The English vocabulary the corpus actually uses for each kind of question.
INTENT_EXPANSION = {
    "overview": (
        "general information overview about the organization its main purpose "
        "programs tracks specializations training duration training type "
        "target audience eligibility requirements and how to apply"
    ),
    "comparison": (
        "programs tracks training duration eligibility requirements "
        "target audience overview"
    ),
    "duration": "duration months weeks hours training period program length",
    "eligibility": (
        "eligibility requirements admission criteria who can apply "
        "application process registration"
    ),
    "tracks": "tracks programs specializations courses diploma training fields",
    "specific": "",
}

# Arabic terms whose English equivalent is what the documents are written with.
GLOSSARY = {
    "مدة": "duration",
    "ساعات": "hours",
    "شهور": "months",
    "شهر": "month",
    "اسبوع": "week",
    "تراك": "track",
    "تراكات": "tracks",
    "مسار": "track",
    "مسارات": "tracks",
    "برنامج": "program",
    "برامج": "programs",
    "تخصص": "specialization",
    "تخصصات": "specializations",
    "شروط": "requirements",
    "متطلبات": "requirements",
    "قبول": "admission",
    "تقديم": "application apply",
    "تسجيل": "registration",
    "تدريب": "training",
    "مجاني": "free",
    "شهادة": "certificate",
    "منحة": "scholarship",
    "خريجين": "graduates",
    "طلاب": "students",
    "مقر": "headquarters location",
    "فروع": "branches",
    "مكافأة": "stipend",
}
_GLOSSARY_NORMALIZED = {normalize(term): english for term, english in GLOSSARY.items()}

ORG_LABELS = {"iti": "ITI", "nti": "NTI", "depi": "DEPI", "itida": "ITIDA"}


def detect_language(text: str) -> str:
    """Return the user's reply language (``ar`` or ``en``).

    Script is the reliable signal for Arabic written with an English track name;
    ``langdetect`` handles pure Latin questions and mixed edge cases.  Anything
    other than Arabic is treated as English because the product supports these
    two reply languages only.
    """
    arabic = len(_ARABIC.findall(text))
    latin = len(_LATIN.findall(text))
    if arabic >= max(3, latin * 0.2):
        return "ar"
    if detect_langdetect:
        try:
            return "ar" if detect_langdetect(text) == "ar" else "en"
        except LangDetectException:
            pass
    return "en" if latin else "ar"


def classify_intent(question: str) -> str:
    """One of: overview, comparison, duration, eligibility, tracks, specific."""
    normalized = normalize(question)
    for intent, markers in INTENT_MARKERS:
        if _matches(markers, normalized):
            return intent
    if _matches(WEAK_OVERVIEW_MARKERS, normalized):
        return "overview"
    return "specific"


def expand_query(question: str, intent: str, organizations: set[str]) -> str:
    """The question plus the English terms that its intent is written with."""
    parts = [question]
    parts.extend(ORG_LABELS.get(org, org.upper()) for org in sorted(organizations))

    normalized = normalize(question)
    parts.extend(
        english for term, english in _GLOSSARY_NORMALIZED.items() if term in normalized
    )

    expansion = INTENT_EXPANSION.get(intent, "")
    if expansion:
        parts.append(expansion)
    return " ".join(part for part in parts if part)


# --- matching the names the knowledge base knows -----------------------------
@lru_cache(maxsize=1)
def known_names() -> tuple[tuple[str, str, str], ...]:
    """(normalised form, original name, kind) for every program/track/specialisation.

    Read from the knowledge-base files so the names come from the documents rather
    than from a list maintained by hand. Longest first, so "Data Science" wins over
    "Data" and "Full Stack .Net Web Developer" over "Full Stack".
    """
    names: dict[str, tuple[str, str]] = {}
    for path in sorted(KNOWLEDGE_FOLDER.glob("*_knowledge.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                node = json.load(f)
        except Exception:
            continue                      # a missing/broken file just means no matching
        for name in node.get("programs", {}):
            names.setdefault(name, (name, "program"))
        for track, facts in node.get("tracks", {}).items():
            names.setdefault(track, (track, "track"))
            for specialization in facts.get("specializations", []):
                names.setdefault(specialization, (specialization, "specialization"))

    resolved = []
    for name, (original, kind) in names.items():
        normalized = normalize(name).strip()
        if len(normalized) >= 4:          # "AI" alone is too short to match safely
            resolved.append((normalized, original, kind))
    return tuple(sorted(resolved, key=lambda item: -len(item[0])))


@lru_cache(maxsize=1)
def names_by_org() -> tuple[tuple[str, str], ...]:
    """(track/program/specialisation name, the one org whose knowledge file
    states it) for every name long enough to match safely.

    Separate from `known_names()`, which drops the org on purpose (it exists to
    boost a chunk by name regardless of which org it belongs to) - this exists
    for the opposite job: telling a name that genuinely belongs to org A apart
    from one that belongs to org B, when a generated answer must be checked for
    content it pulled in from the wrong one. A name two orgs happen to share is
    dropped rather than attributed to either - it cannot then falsely flag
    either org's real answer as contaminated.
    """
    owner: dict[str, str | None] = {}
    for path in sorted(KNOWLEDGE_FOLDER.glob("*_knowledge.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                node = json.load(f)
        except Exception:
            continue
        org = path.stem.replace("_knowledge", "")
        names = set(node.get("programs", {}))
        for track, facts in node.get("tracks", {}).items():
            names.add(track)
            names.update(facts.get("specializations", []))
        for name in names:
            owner[name] = None if name in owner else org

    return tuple(
        (name, org) for name, org in owner.items()
        if org is not None and len(name) >= 4
    )


def foreign_track_names(answer: str, allowed_orgs: set[str]) -> set[str]:
    """Names of tracks/programs/specialisations the answer states that belong to
    an organisation NOT among the retrieved sources.

    Catches a failure `_foreign_orgs`-style checking (in generate_answer.py)
    cannot: the model naming another organisation's real track/job-profile
    content without ever writing that organisation's name - confirmed
    happening when conversation history held an earlier turn's answer about a
    different organisation, and the model blended its track names into a new
    answer whose retrieved sources were correctly scoped to only the org asked
    about this time.
    """
    if not allowed_orgs:
        return set()
    lowered = answer.lower()
    all_names = names_by_org()

    # A name from an allowed org can contain a foreign org's shorter name as a
    # plain substring - DEPI's track is literally "Digital Arts", and ITI's is
    # "Digital Arts & 3D Animation". An answer correctly describing ITI's own
    # track then contains DEPI's exact name too, purely as a prefix match; that
    # is not contamination. Once a longer allowed-org name is confirmed present,
    # any foreign name that is only a substring of it is cleared, not flagged.
    allowed_present = [n for n, org in all_names if org in allowed_orgs and n.lower() in lowered]

    return {
        name for name, org in all_names
        if org not in allowed_orgs and name.lower() in lowered
        and not any(name.lower() in allowed.lower() for allowed in allowed_present)
    }


def detect_names(question: str) -> dict[str, str]:
    """The track / program / specialisation a question names, if any.

    "ممكن أعرف مدة الـData Science track في ITI؟" resolves to
    {"track": "Data Science"}, which retrieval then prefers over every other ITI
    chunk - the difference between answering about Data Science and answering
    about whichever ITI track happened to word-match.
    """
    normalized = normalize(question)
    found: dict[str, str] = {}
    for candidate, original, kind in known_names():
        if kind not in found and f" {candidate} " in normalized:
            found[kind] = original
    if "program" not in found:
        for alias, program in _PROGRAM_ALIASES_NORMALIZED:
            if alias in normalized:
                found["program"] = program
                break
    return found


# Arabic names users type for programmes whose documents are English. Without
# this, "مدة التدريب الصيفي في NTI قد إيه؟" named no programme, so retrieval
# preferred two context-free NTI Q&A pairs ("مدتها قد إيه؟ -> 4 شهور ...", about
# a different programme) over the Private Summer Training card, and the model
# blended the two into a wrong answer. The value is deliberately the shared part
# of the programme names ("Summer Training"): retriever._names_match compares by
# substring, so it matches NTI's "Private Summer Training" and ITIDA's "Student
# Summer Training" alike, and the organisation named in the question decides.
_PROGRAM_ALIASES = {
    "التدريب الصيفي": "Summer Training",
    "تدريب صيفي": "Summer Training",
    "الصيفي": "Summer Training",
    "summer training": "Summer Training",
    "برنامج الـ 9 شهور": "Professional Training Program",
    "برنامج التسع شهور": "Professional Training Program",
    "كود كامب": "Intensive Code Camp",
    "code camp": "Intensive Code Camp",
}
_PROGRAM_ALIASES_NORMALIZED = tuple(
    (normalize(alias), program) for alias, program in _PROGRAM_ALIASES.items()
)


# A rule table cannot normalise a question built from words it has never seen.
# When the question names no organisation and no known program or track, there is
# nothing to anchor retrieval to, and an LLM rewrite is worth its latency; when it
# does name them, the rules already have what they need and the call is skipped.
# See `05_generation/generate_answer.py`, which owns the LLM call itself.
def should_rewrite(plan: dict) -> bool:
    """Whether an LLM rewrite of this question would add anything."""
    if plan.get("organizations") or plan.get("track") or plan.get("program"):
        return False
    return len(plan.get("question", "")) > 12


def analyze(question: str) -> dict:
    """Everything retrieval needs to know about a question, in one pass.

    Returns the `language` to answer in, the `intent`, the `organizations` and any
    program/track named, the `categories` of chunk that answer this kind of
    question, the `search_query` to embed and match on, the `top_k` this kind of
    question needs, and the `max_per_source` / `max_per_category` caps (0 =
    unlimited) that stop a broad answer being built out of one page repeated.
    """
    question = (question or "").strip()
    organizations = detect_organizations(question)
    intent = classify_intent(question)
    named = detect_names(question)

    # Only expand when the question is anchored to a known organisation - see
    # the module docstring for why this guard matters to the refusal gate.
    expand = bool(organizations) and intent in EXPAND_INTENTS
    search_query = expand_query(question, intent, organizations) if expand else question

    plan = {
        "question": question,
        "language": detect_language(question),
        "intent": intent,
        "organizations": organizations,
        "categories": INTENT_CATEGORIES.get(intent, ()),
        "track": named.get("track", ""),
        "program": named.get("program", ""),
        "specialization": named.get("specialization", ""),
        "search_query": search_query,
        "expanded": search_query != question,
        "top_k": TOP_K_BY_INTENT.get(intent, DEFAULT_TOP_K),
        "max_per_source": MAX_CHUNKS_PER_SOURCE.get(intent, 0),
        "max_per_category": MAX_CHUNKS_PER_CATEGORY.get(intent, 0),
    }
    plan["needs_rewrite"] = should_rewrite(plan)
    return plan
