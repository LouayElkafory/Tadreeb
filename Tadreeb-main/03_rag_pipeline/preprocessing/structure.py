"""
Turns a plain chunk of text into a *structured* one: which organisation it
belongs to, which program and track it describes, what category of question it
can answer, and any duration / training type it states.

Why this exists
---------------
Every chunk used to carry only `org`, `document` and `page`. That is enough to
find text that looks like the question, but not enough to answer questions of
the shape "how long is the Data Science track at ITI" - the retriever had no way
to tell a chunk that *states a duration* apart from one that merely mentions the
track. Categorising chunks, and tagging them with the program/track they belong
to, is what lets retrieval prioritise `org=ITI, category=duration,
track=Data Science` instead of hoping the wording matches.

How it extracts
---------------
Deterministically, from patterns the source documents actually use - never by
guessing. The corpus is regular enough for this:

* ITI's track brochures all carry `TOTAL HOURS 1,180hrs` and
  `DELIVERY Blended Online & on-site`, and open with "The <Name> Track ...".
* DEPI's catalogue pages open with `SOFTWARE DEVELOPMENT TRACK` and number their
  job profiles `1. DevOps Engineer`.
* ITIDA and NTI state their programme lengths inline ("lasts for 120 hours",
  "Train To Hire (4 Month)").

Anything a document does not state is left out. A missing duration stays
missing; it is never inferred from a similar track.

Used by `embed_and_store.py` (so a full rebuild keeps the structure),
`01_scraping/collect_web_data.py` (web pages), and
`03_rag_pipeline/embeddings/backfill_structure.py` (existing chunks, metadata
only).
"""
import re

# The question categories retrieval can prioritise. `general` is the fallback
# for text that answers nothing in particular.
CATEGORIES = (
    "organization_info",
    "programs",
    "tracks",
    "duration",
    "training_type",
    "eligibility",
    "application",
    "general",
)

# --- category classification ------------------------------------------------
# Each category has strong markers (worth 3) and weak ones (worth 1). A chunk
# gets every category it scores on; the highest score becomes its primary
# `category`, and the full set is kept in `categories` so a question about
# duration still reaches a chunk whose main subject is the track.
_MARKERS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "duration": (
        ("total hours", "program content", "duration", "مدة", "مدته", "مدتها",
         "lasts for", "عدد الساعات", "إجمالي الساعات"),
        ("hours", "hrs", "months", "month", "weeks", "ساعة", "ساعه", "شهر",
         "أشهر", "اشهر", "شهور", "اسبوع"),
    ),
    "training_type": (
        ("delivery", "blended", "on-site", "onsite", "in-person", "hybrid",
         "أونلاين", "حضوري", "عن بعد", "اون لاين"),
        ("online training", "online courses", "self-paced", "instructor-led",
         "remotely", "distance learning"),
    ),
    "eligibility": (
        ("eligibility", "eligible", "university grade", "prerequisite",
         "requirements", "required grade", "شروط", "متطلبات", "مؤهل",
         "شروط القبول", "الفئة المستهدفة"),
        ("graduates of", "faculty of", "bachelor", "fresh graduates",
         "target audience", "خريجي", "حديثي التخرج", "بكالوريوس"),
    ),
    "application": (
        ("how to apply", "application process", "admission process", "apply now",
         "registration", "deadline", "التقديم", "التسجيل", "كيفية التقديم"),
        ("apply", "application", "admission", "interview", "selection",
         "entrance exam", "المقابلة", "اختبار القبول", "الأوراق المطلوبة"),
    ),
    "tracks": (
        ("track", "tracks", "specialization", "specialisation", "specialty",
         "مسار", "مسارات", "تراك", "تراكات", "تخصص", "تخصصات"),
        ("job profiles", "profile", "pillar", "مجال"),
    ),
    "programs": (
        ("professional training program", "intensive code camp", "diploma",
         "training program", "برنامج تدريبي", "برامج", "دبلومة"),
        ("program", "programme", "course", "academy", "initiative", "برنامج",
         "كورس", "أكاديمية", "مبادرة"),
    ),
    "organization_info": (
        ("about us", "what we do", "vision", "mission", "established",
         "affiliated", "عبارة عن", "تأسس", "تابعة", "يهدف", "تهدف", "نبذة"),
        ("ministry", "agency", "institute", "governmental", "egypt",
         "وزارة", "هيئة", "معهد", "مصر"),
    ),
}

_STRONG, _WEAK = 3, 1


def classify(text: str) -> tuple[str, list[str]]:
    """(primary category, every category the chunk scores on)."""
    lowered = (text or "").lower()
    scores: dict[str, int] = {}
    for category, (strong, weak) in _MARKERS.items():
        score = sum(_STRONG for marker in strong if marker in lowered)
        score += sum(_WEAK for marker in weak if marker in lowered)
        if score:
            scores[category] = score

    if not scores:
        return "general", ["general"]

    # Ties break by CATEGORIES order, which puts the specific categories
    # (duration, training_type, eligibility) ahead of the broad ones.
    ordered = sorted(scores, key=lambda c: (-scores[c], CATEGORIES.index(c)))
    return ordered[0], ordered


# --- track / program extraction ---------------------------------------------
# A candidate track name has to look like a name: every word capitalised, an
# acronym, a number, or a small connector. Without that, "complete architectural
# journey. This track" yields "complete architectural journey. This".
_CONNECTORS = {"and", "of", "for", "the", "&", "-", "/", "with", "in"}
_NAME_WORD = re.compile(r"^[A-Z0-9(][\w&/\.\-()\+]*$")
# A capitalised word at the start of a sentence is not a name: "This track
# equips participants..." and "Each track lasts..." both match the pattern
# otherwise, and produced tracks literally called "This" and "Each".
_NOT_A_NAME = {
    "the", "this", "that", "these", "those", "each", "every", "it", "its",
    "a", "an", "our", "their", "his", "her", "all", "both", "another", "such",
    "any", "one", "second", "first", "other", "same", "new", "only",
}

_TRACK_PATTERNS = (
    # NTI Private Summer Training's official tracks page uses numbered headings
    # rather than the word "track": "1. Telecom Engineering: ...".  Keep the
    # alternatives explicit so ordinary numbered sentences are never promoted
    # into a track name.
    re.compile(
        r"(?:^|\s)\d+\.\s+"
        r"(Telecom Engineering|System Engineering|Software Engineering|"
        r"Network Engineering|Data Engineering|Electronics and Embedded Systems)\s*:",
        re.I,
    ),
    # ITI brochures: "... JUL 2026 The Data Science track develops ..."
    re.compile(r"(?:^|[.\n]|\d{4})\s*(?:The\s+)([A-Za-z0-9][\w&/\.\-() \+]{2,55}?)\s+[Tt]rack\b"),
    # DEPI catalogue page headers: "SOFTWARE DEVELOPMENT TRACK"
    re.compile(r"\b([A-Z][A-Z0-9&/\-. ]{3,55}?)\s+TRACK\b"),
    # "Embedded & Edge Architectures track is a large-scale diploma program"
    re.compile(r"(?:^|[.\n]|\d{4})\s*([A-Z][\w&/\.\-() \+]{2,55}?)\s+[Tt]rack\b"),
)

# DEPI numbers its job profiles under a track header: "1. DevOps Engineer". The
# cleaner collapses newlines, so by the time we see it the number is mid-line
# ("SOFTWARE DEVELOPMENT TRACK 1. DevOps Engineer ..."); anchoring on \n matched
# nothing at all, which left every DEPI track with no specialisations.
_PROFILE_PATTERN = re.compile(r"(?:^|\s)\d{1,2}\.\s+([A-Z][\w&/\.\- ]{3,50})")
# One profile's name runs into the next item's number on a collapsed line
# ("1. DevOps Engineer 2. React Frontend Web Developer", "... Designer 17 4. ...").
# Cut at the first standalone number - but not at one glued to a letter, or
# "Professional 3D & VR Designer" would be truncated to "Professional".
_NEXT_ITEM = re.compile(r"\s+\d+(?![A-Za-z])")
# The catalogue restates the name in the sentence that follows it ("3. Cisco
# Cybersecurity Engineer A Cisco Cybersecurity Engineer is responsible for...").
# Every word there is capitalised, so the name check cannot tell where the name
# ends - the article that opens the sentence can.
_SENTENCE_START = re.compile(r"\s+(?:A|An|The|This|These|It|Its)\s+[A-Z]")

# Program names the corpus actually uses, matched literally.
_PROGRAM_NAMES = (
    "Professional Training Program",
    "Intensive Code Camp",
    "Student Summer Training",
    "Train to Hire",
    "Summer Training",
    "Vendor Academies",
    "HireReady",
    "Wazeefa-Tech",
    "Creativa",
    "Digital Egypt Youth",
    "Mahara-Tech",
    "AI Academy",
)


def _looks_like_a_name(candidate: str) -> bool:
    words = candidate.split()
    if not 1 <= len(words) <= 7:
        return False
    if words[0].lower() in _NOT_A_NAME or candidate.lower() in _NOT_A_NAME:
        return False
    return all(w.lower() in _CONNECTORS or _NAME_WORD.match(w) for w in words)


def _tidy(candidate: str) -> str:
    candidate = candidate.strip(" .,-–—:")
    # Brochure headers leak into the match: "PROFESSIONAL TRAINING PROGRAM LAST
    # UPDATED: JUL 2026 The Data Science" -> "Data Science".
    for noise in ("LAST UPDATED", "PROFESSIONAL TRAINING PROGRAM"):
        if noise in candidate.upper():
            candidate = candidate[candidate.upper().rfind(noise) + len(noise):]
    return candidate.strip(" .,-–—:")


def _normalize_case(shouted: str) -> str:
    """"AI & DATA SCIENCE" -> "AI & Data Science" (plain .title() gives "Ai")."""
    return " ".join(
        word if (len(word) <= 3 and word.isalpha()) or not word.isalpha() else word.title()
        for word in shouted.split()
    )


def extract_track(text: str) -> str:
    """The track this text is about, or "" when it does not name one."""
    for pattern in _TRACK_PATTERNS:
        for match in pattern.finditer(text or ""):
            candidate = _tidy(match.group(1))
            if candidate and _looks_like_a_name(candidate):
                return _normalize_case(candidate) if candidate.isupper() else candidate
    return ""


def extract_specialization(text: str) -> str:
    """The first numbered job profile in the text (DEPI's catalogue shape)."""
    found = extract_specializations(text)
    return found[0] if found else ""


def extract_specializations(text: str) -> list[str]:
    """Every numbered job profile the text lists, in order, deduplicated.

    A table of contents is skipped: it lists the profiles of all six DEPI tracks
    under whichever track header happens to appear first on the page, so reading
    it attributes "Graphics Designer" to the AI & Data Science track.
    """
    if "contents" in (text or "")[:60].lower():
        return []
    # A chunk straddling two catalogue sections would hand the second section's
    # profiles to the first section's track.
    if len(set(_TRACK_PATTERNS[1].findall(text or ""))) > 1:
        return []

    found: list[str] = []
    for match in _PROFILE_PATTERN.finditer(text or ""):
        # A contents line leaves the page number attached: "DevOps Engineer 7".
        candidate = _NEXT_ITEM.split(match.group(1).strip(" .,-"))[0]
        candidate = _SENTENCE_START.split(candidate)[0].strip(" .,-")
        if candidate and _looks_like_a_name(candidate) and candidate not in found:
            found.append(candidate)
    return found


def extract_program(text: str) -> str:
    """A program name the corpus states literally, or ""."""
    lowered = (text or "").lower()
    for name in _PROGRAM_NAMES:
        if name.lower() in lowered:
            return name
    return ""


# --- duration / training type ------------------------------------------------
_DURATION_PATTERNS = (
    re.compile(r"TOTAL HOURS\s*([\d,]+)\s*(hrs|hours)", re.I),
    re.compile(r"(?:program content|content)\s*[-–—]\s*([\d,]+)\s*(hours|hrs)", re.I),
    re.compile(r"lasts? for\s*([\d,]+)\s*(hours|hrs|months?|weeks?)", re.I),
    re.compile(r"\b(?:is a|is an)\s*([\d,]+)[-\s]?(month|week|hour)s?\b", re.I),
    re.compile(r"\(\s*([\d,]+)\s*(Month|Months|Week|Weeks|Hour|Hours)\s*\)", re.I),
    re.compile(r"([\d,]+)\s*(ساعة|ساعه)"),
    re.compile(r"([\d,]+)\s*(شهر|أشهر|اشهر|شهور)"),
)

_UNIT_CANONICAL = {
    "hr": "hours", "hrs": "hours", "hour": "hours", "hours": "hours",
    "month": "months", "months": "months", "week": "weeks", "weeks": "weeks",
    "ساعة": "hours", "ساعه": "hours",
    "شهر": "months", "أشهر": "months", "اشهر": "months", "شهور": "months",
}


def extract_duration(text: str) -> tuple[str, str]:
    """(value, unit) as the text states it, e.g. ("1,180", "hours"). ("", "") if absent."""
    for pattern in _DURATION_PATTERNS:
        match = pattern.search(text or "")
        if match:
            value, unit = match.group(1).strip(), match.group(2).strip().lower()
            return value, _UNIT_CANONICAL.get(unit, unit)
    return "", ""


# Ordered: a page saying "Blended Online & on-site" is blended, not online.
_TRAINING_TYPES = (
    ("blended", ("blended", "hybrid", "مدمج", "هجين")),
    ("onsite", ("on-site", "onsite", "in-person", "on site", "حضوري", "وجاهي")),
    ("online", ("online", "remote", "virtual", "أونلاين", "اون لاين", "عن بعد")),
    ("self-paced", ("self-paced", "self paced")),
)


# The word "online" turns up in passing all over the corpus ("apply online", "the
# online platform", "online payment"), so a bare mention says nothing about how a
# programme is delivered. A delivery mode is read only from ITI's `DELIVERY` field
# or from a phrase that is explicitly about the training - matching loosely tagged
# 1,658 of 1,671 chunks with a training type, which made the field meaningless.
_DELIVERY_FIELD = re.compile(r"delivery\s*([^\n]{0,60})", re.I)
_SUBJECT = r"training|courses?|classes|program(?:me)?s?|sessions?|study|learning|تدريب|دراسة|تعلم"
_MODE = (r"blended|hybrid|on-?site|on site|in-person|online|remote(?:ly)?|self-?paced"
         r"|أونلاين|اون لاين|حضوري|عن بعد")
_DELIVERY_PHRASES = re.compile(
    rf"(?:{_SUBJECT})[^.\n]{{0,40}}?(?:{_MODE})|(?:{_MODE})[^.\n]{{0,25}}?(?:{_SUBJECT})",
    re.I,
)


def delivery_field(text: str) -> str:
    """The training type stated in an explicit `DELIVERY ...` field, or "".

    Kept separate because it is the authoritative statement: every ITI track
    brochure has one, and `document_profiles` trusts it over a passing phrase
    elsewhere in the same document.
    """
    field = _DELIVERY_FIELD.search(text or "")
    if not field:
        return ""
    window = field.group(1).lower()
    for name, markers in _TRAINING_TYPES:
        if any(marker in window for marker in markers):
            return name
    return ""


def extract_training_type(text: str) -> str:
    """"blended" / "onsite" / "online" / "self-paced", or "" when unstated."""
    stated = delivery_field(text)
    if stated:
        return stated

    phrase = _DELIVERY_PHRASES.search(text or "")
    if not phrase:
        return ""
    window = phrase.group(0).lower()
    for name, markers in _TRAINING_TYPES:
        if any(marker in window for marker in markers):
            return name
    return ""


# --- document-level rollup ---------------------------------------------------
# A track brochure names its track once, on page 1 ("The Data Science track
# develops..."), and states its hours and delivery mode on a later page. Read
# per chunk, the duration chunk therefore has no track and the track chunk has no
# duration - and "how long is the Data Science track" matches neither. Rolling
# each source document up to one profile, then filling every chunk of that
# document from it, is what connects them:
#
#     ITI -> Professional Training Program -> Data Science
#            -> 1,455 hours -> blended
#
# This is only ever done within a single document, so one track's hours can never
# be attached to another's.
PROFILE_FIELDS = ("program", "track", "duration", "duration_unit", "training_type")


def document_profiles(chunks: list[dict]) -> dict[tuple[str, str], dict]:
    """(org, document) -> the program/track/duration/training type it states.

    Only *single-subject* documents are rolled up: ones that name at most one
    program and at most one track. An ITI track brochure qualifies - it is about
    the Data Science track of the Professional Training Program from cover to
    cover, so its `TOTAL HOURS` belongs to every page of it.

    Documents covering several subjects are left alone, and this is the rule that
    keeps the knowledge base honest. NTI's scraped portal describes six programs
    in one document and states "Train To Hire (4 Month)" in one of them; rolled
    up, that 4 months reached every chunk, and the Creativa program card then
    claimed a duration Creativa's sources never mention. DEPI's catalogue (six
    tracks) and `<org>_qa.jsonl` (hundreds of unrelated answers) are excluded for
    the same reason - each of their chunks states its own subject already.
    """
    seen: dict[tuple[str, str], dict[str, set[str]]] = {}
    stated: dict[tuple[str, str], str] = {}
    for chunk in chunks:
        # The curated Q&A file is one "document" holding hundreds of unrelated
        # answers, and each of those answers is already self-contained. It has no
        # document-level subject to inherit, so it is left out of the rollup.
        if chunk.get("source_type") == "qa":
            continue
        key = (chunk.get("org", ""), chunk.get("document", ""))
        values = seen.setdefault(key, {})
        found = enrich(chunk, profile=None)
        for field in PROFILE_FIELDS:
            if found.get(field):
                values.setdefault(field, set()).add(found[field])
        # An explicit DELIVERY field outranks a phrase found elsewhere in the same
        # document, so a brochure that says "DELIVERY Blended" but also mentions
        # "online application" is still blended rather than losing the field to
        # the disagreement.
        declared = delivery_field(chunk.get("text", ""))
        if declared:
            stated.setdefault(key, declared)

    profiles = {}
    for key, values in seen.items():
        if len(values.get("program", ())) > 1 or len(values.get("track", ())) > 1:
            profiles[key] = {}          # multi-subject document: nothing to inherit
            continue
        profiles[key] = {
            field: next(iter(v)) for field, v in values.items() if len(v) == 1
        }
    for key, declared in stated.items():
        if profiles.get(key):
            profiles[key]["training_type"] = declared
    return profiles


# --- the one entry point other modules use ----------------------------------
# Chroma only stores scalars, so the multi-category list is joined into a string
# and matched by substring at query time.
def enrich(chunk: dict, profile: dict | None = None) -> dict:
    """The structured metadata for a chunk: category, track, program, duration,
    training type. Only fields the text actually supports are returned, so
    `chunk_metadata()` never has to strip empty values.

    `profile` is this chunk's document-level rollup (see `document_profiles`). It
    fills the fields this particular chunk does not state itself - the track name
    for a page that only lists hours, and vice versa.
    """
    text = chunk.get("text", "")
    # The title carries the subject on web pages ("ITIDA Train to Hire Program"),
    # where the body may be mostly navigation.
    subject = f"{chunk.get('title', '')}\n{text}"

    category, categories = classify(subject)
    extra = {"category": category, "categories": ",".join(categories)}

    track = chunk.get("track") or extract_track(text)
    if track:
        extra["track"] = track

    specializations = [s for s in extract_specializations(text) if s != track]
    if specializations:
        extra["specialization"] = specializations[0]
        # The full list is for build_knowledge_base.py; Chroma only takes scalars,
        # so `chunk_metadata()` keeps the first one and drops this.
        extra["specializations"] = specializations

    program = chunk.get("program") or extract_program(subject)
    if program:
        extra["program"] = program

    value, unit = extract_duration(text)
    if value:
        extra["duration"] = f"{value} {unit}".strip()
        extra["duration_unit"] = unit

    training_type = extract_training_type(text)
    if training_type:
        extra["training_type"] = training_type

    # Fall back to what the rest of the document established.
    for field in (profile or {}):
        if field not in extra and profile[field]:
            extra[field] = profile[field]

    return extra
