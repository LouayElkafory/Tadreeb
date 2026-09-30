"""
Detects Arabic text that came out of a PDF in visual (painted) order instead of
logical reading order. Shared by the extractor and the cleaning step so both
agree on what "broken" looks like.
"""
import re

ARABIC_RANGE = re.compile(r"[؀-ۿ]")

# Frequent Arabic function words. Their *reversed* spellings are not real words,
# so they only show up as standalone tokens when a page is visually ordered.
# Word boundaries matter: "نم" (reversed "من") is a common bigram *inside*
# ordinary Arabic words, so substring counting false-positives on good text.
_MARKERS = ["في", "من", "على", "التي", "الذي", "عن", "إلى", "مع", "هذا",
            "كل", "بين", "التدريب", "المعهد", "وزارة", "قال", "أن"]


def _count_words(text: str, words: list[str]) -> int:
    pattern = r"(?<![؀-ۿ])(?:" + "|".join(re.escape(w) for w in words) + r")(?![؀-ۿ])"
    return len(re.findall(pattern, text))


def is_visually_ordered(text: str) -> bool:
    """True when Arabic text reads backwards (PDF glyph order, not logical order)."""
    if len(ARABIC_RANGE.findall(text)) < 30:
        return False  # too little Arabic to judge; leave it alone
    forward = _count_words(text, _MARKERS)
    backward = _count_words(text, [w[::-1] for w in _MARKERS])
    return backward > forward
