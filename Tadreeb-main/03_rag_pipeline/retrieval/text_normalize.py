"""
Tokenisation and Arabic folding used by the lexical half of retrieval.

The corpus is mostly English PDF text while users ask in Egyptian Arabic, and
Arabic spelling varies freely across sources (alef with/without hamza, ta marbuta
vs ha, alef maqsura vs ya, diacritics). Folding those variants before keyword
matching is what makes "المبادره" match "المبادرة". This is applied to the query
and to the chunk text symmetrically, and never to the text shown to the LLM.
"""
import re

_DIACRITICS = re.compile("[ً-ٰٟـ]")
_TOKEN = re.compile(r"[0-9A-Za-z\u0621-\u064A\u0660-\u0669]+")  # letters/digits only - Arabic punctuation (، ؛ ؟) must not glue onto a term

# Very frequent words that carry no retrieval signal in either language.
STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "for", "to", "is", "are", "and", "or",
    "what", "how", "many", "much", "do", "does", "with", "by", "at", "it", "its",
    "في", "من", "علي", "الي",
    "عن", "مع", "هل", "ايه",
    "اي", "ايهي", "هو", "هي",
    "ده", "دي", "كام", "ايهو",
    "و", "يعني", "طب", "اللي",
    "ما", "ازاي", "امتي", "فيه", "ليه",
}


def fold_arabic(text: str) -> str:
    """Collapse Arabic orthographic variants to one canonical spelling."""
    text = _DIACRITICS.sub("", text)
    text = text.replace("ى", "ي")            # alef maqsura -> ya
    text = text.replace("ة", "ه")            # ta marbuta   -> ha
    for alef in "آأإ":
        text = text.replace(alef, "ا")            # hamza alef   -> bare alef
    text = text.replace("ؤ", "و").replace("ئ", "ي")
    return text


# Arabic attaches the definite article and several prepositions/conjunctions
# directly to the word, so "مقر" (headquarters) and "المقر" (the headquarters) are
# different tokens to an exact-match index - a question asking "فين مقر ITI"
# scored zero against the chunk that answers it. Light stemming strips those
# clitics so the two forms meet. It runs on the query and on the indexed text
# alike; anything it gets wrong, it gets wrong on both sides.
_PREFIXES = ("وال", "بال", "كال", "فال", "ال", "لل", "و")
_SUFFIXES = ("ها", "ات", "ون", "ين", "يه", "هم", "كم", "نا", "ه")
MIN_STEM = 3


def light_stem(token: str) -> str:
    """Strip Arabic clitics, but never down to an unrecognisable stub."""
    for prefix in _PREFIXES:
        if token.startswith(prefix) and len(token) - len(prefix) >= MIN_STEM:
            token = token[len(prefix):]
            break
    for suffix in _SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= MIN_STEM:
            token = token[: -len(suffix)]
            break
    return token


def tokenize(text: str, drop_stopwords: bool = True, stem: bool = True) -> list[str]:
    """Fold, lowercase, split and lightly stem text into comparable terms."""
    tokens = _TOKEN.findall(fold_arabic(text.lower()))
    if drop_stopwords:
        tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    if stem:
        tokens = [light_stem(t) for t in tokens]
    return tokens
