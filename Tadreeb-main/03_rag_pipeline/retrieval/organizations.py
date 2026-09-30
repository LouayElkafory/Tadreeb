"""
Recognises which training organisation a question is about.

The four programmes are distinct - a question about ITI's intake month must not
be answered from NTI's material - but their material is similar enough that
dense similarity happily returns the wrong one. Detecting the organisation from
the question and preferring its chunks fixes that.

Matching is on tokens, not substrings, so "ITIDA" is never read as "ITI".
"""
from text_normalize import tokenize

# Token -> organisation. Arabic aliases matter as much as the acronyms, since
# users usually write the institute's full name rather than the abbreviation.
ALIASES: dict[str, tuple[str, ...]] = {
    "iti": (
        "iti",
        "معهد تكنولوجيا المعلومات",
    ),
    "nti": (
        "nti",
        "المعهد القومي للاتصالات",
        "القومي للاتصالات",
    ),
    "depi": (
        "depi",
        "رواد مصر الرقمية",
    ),
    "itida": (
        "itida",
        "هيئة تنمية صناعة تكنولوجيا المعلومات",
    ),
}


def detect_organizations(question: str) -> set[str]:
    """Organisations explicitly named in a question (may be empty, or several)."""
    tokens = tokenize(question, drop_stopwords=False)
    token_set = set(tokens)
    joined = " ".join(tokens)

    found = set()
    for org, aliases in ALIASES.items():
        for alias in aliases:
            alias_tokens = tokenize(alias, drop_stopwords=False)
            if len(alias_tokens) == 1:
                if alias_tokens[0] in token_set:
                    found.add(org)
                    break
            elif " ".join(alias_tokens) in joined:
                found.add(org)
                break
    return found
