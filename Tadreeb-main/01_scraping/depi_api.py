"""
DEPI-only: collects structured programme data directly from DEPI's own backend
API, instead of scraping https://depi.gov.eg/ (a JavaScript single-page app that
serves an empty HTML shell to any client that doesn't run its JS).

Root cause fix, not a workaround: the DEPI site itself calls
`https://be.eeds.gov.eg/api/GenericPage/GetPageByString?pageUrl=<slug>` to fill
that shell in. That endpoint is a plain, unauthenticated JSON REST API - no
JavaScript execution needed on our side, no Playwright/browser dependency. This
was found by rendering depi.gov.eg with Playwright once, during development, and
inspecting the network requests it made; the finding is reproducible with any
browser's devtools (Network tab, filter "eeds"), and does not need a browser to
use afterwards.

Why this is a better source than the 2024 PDF catalogue already in the corpus
(`02_data/01_raw/depi/official/*.pdf`): the API returns the CURRENT programme
structure as clean, machine-readable HTML - `<table>` rows pairing a track with
its job profiles, and `<div class="track-card">` blocks with labelled fields
(Overview, Who is this track for?, Delivery Approach, ...) - rather than prose
that has to be reverse-engineered with regexes. Every specialisation this module
emits comes from ONE table row (`<tr><td>Track</td><td>Job Profile</td></tr>`);
there is no free-text boundary to get wrong, so there is no "ambiguous chunk"
case to skip. Every specialisation/track/profile visible on the site is turned
into a record - nothing is dropped for being hard to parse. A field the source
does not state is written as "Not specified in source", never guessed.

DEPI currently runs two parallel programmes, both covered here:

* "DEPI"          (https://depi.gov.eg/depi)          - 7 tracks, 31 job profiles
* "DEPI Industry" (https://depi.gov.eg/depiindustry)  - 6 job profiles, no further
                                                         track subdivision (treated
                                                         as one umbrella track,
                                                         named "DEPI Industry")

Usage (also called from `collect_web_data.py`'s DEPI branch):

    from depi_api import collect_depi_pages
    pages = collect_depi_pages()   # -> list[dict], the page schema collect_web_data.py uses

Every dict already carries the *known* structured fields - `program`, `track`,
`specialization`, `category`, `categories`, `duration`, `duration_unit`,
`training_type` - set directly from the source, not inferred. The caller must
NOT re-run them through `structure.py`'s regex-based `enrich()`/`extract_*()`:
that would re-derive these same fields from prose and risks overwriting a
correct, source-verified value with a worse guess.
"""
import re
import sys
from html import unescape
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scraper_utils import logger  # noqa: E402

# Deliberately NOT scraper_utils.HEADERS: it sends "Accept-Language: ar,en-US;q=0.7"
# (tuned for the mostly-Arabic sites the other scrapers target), and this API
# honours that - every field name this module parses ("Initiative Tracks",
# "Overview", "Delivery Approach", ...) came back Arabic under those headers,
# which silently broke every regex here. This corpus's DEPI material is English
# (the PDF catalogues are English), so English is requested explicitly.
API_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

API_URL = "https://be.eeds.gov.eg/api/GenericPage/GetPageByString"
SITE_BASE = "https://depi.gov.eg"
REQUEST_TIMEOUT = 20

# slug -> (program name, canonical org-facing URL)
PROGRAM_PAGES = {
    "depi": ("DEPI", f"{SITE_BASE}/depi"),
    "depiindustry": ("DEPI Industry", f"{SITE_BASE}/depiindustry"),
}
ABOUT_SLUG = "aboutdepi"
ABOUT_URL = f"{SITE_BASE}/aboutdepi"

# The CMS displays each track under two different names depending on section -
# a short form in the Track/Job-Profile table ("AI & data Science") and a longer
# one on its overview card ("Artificial Intelligence and Data Science"). Verified
# by comparing both sections of https://depi.gov.eg/depi on 2026-09-25. The table
# name is treated as canonical (it is what "31 job profiles" is counted against);
# this map only decides which overview card's text attaches to which canonical
# track, so a track's Overview/Eligibility text lands under the same track name
# its specialisations are filed under.
# The table itself is inconsistently capitalised ("AI & data Science",
# "InfraStructure & Security" - both verified verbatim from the live API on
# 2026-09-25). Normalised to Title Case here so this is the ONE place a track
# name is decided, rather than leaving two capitalisations of the same track to
# be read as two different tracks by anything that groups records by name -
# including the 2024 PDF catalogue already in the corpus, which spells both of
# these correctly and would otherwise never merge with the API's version.
_TRACK_NAME_FIXES = {
    "ai & data science": "AI & Data Science",
    "infrastructure & security": "Infrastructure & Security",
}
TRACK_CARD_ALIASES = {
    "artificial intelligence and data science": "AI & Data Science",
    "infrastructure and cybersecurity": "Infrastructure & Security",
    "creative digital marketing and digital arts": "Digital Arts",
    "digital game design and development": "Digital Game Creation",
    # These three already match the table's name exactly.
    "management & erp": "Management & ERP",
    "software development": "Software Development",
    "data analytics": "Data Analytics",
}

NOT_SPECIFIED = "Not specified in source"


# --- HTML helpers -------------------------------------------------------------
_STYLE_BLOCK = re.compile(r"<style[^>]*>.*?</style>", re.S | re.I)


def strip_tags(fragment: str) -> str:
    """Plain readable text from an HTML fragment: tags removed, entities decoded.

    Every section's content is a full inline HTML snippet with its own <style>
    block up front (the CMS ships one per section). A tag-only strip leaves that
    block's CSS *text* behind - `re.sub(r"<[^>]+>", ...)` only removes the angle
    brackets, not the declarations between them - so the page's own stylesheet
    was ending up as the first 500+ characters of every extracted field. The
    style block is dropped whole, before tags are stripped from what's left.
    """
    text = _STYLE_BLOCK.sub(" ", fragment or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return unescape(" ".join(text.split()))


def parse_table_rows(content_html: str) -> list[tuple[str, str]]:
    """(track, job_profile) pairs from the first <table> in the HTML.

    The source table leaves a track's cell blank on every row after its first
    (a standard merged-cell rendering), so the track name is carried forward to
    the following blank cells - the same rule a human reads the table with, and
    the only correct one: nothing here is inferred from prose, only from which
    cell in which row explicitly named a track.

    Column order is read from the header row rather than assumed: the main
    "Initiative Tracks" table is (Track Name, Job Profile Name), but the
    per-college "Program Available For each College" tables are the reverse,
    (Job Profile Name, Track Name). Trusting a fixed position here silently
    swapped the two on the per-college tables - every profile came back labelled
    with a track name instead of its own name.

    A single-column table (DEPI Industry has no separate track column) yields
    every row as a profile with an empty track, which the caller assigns to that
    programme's one umbrella track.
    """
    table_match = re.search(r"<table.*?</table>", content_html, re.S)
    if not table_match:
        return []

    rows: list[list[str]] = []
    for tr in re.findall(r"<tr.*?>(.*?)</tr>", table_match.group(0), re.S):
        cells = [strip_tags(cell) for cell in re.findall(r"<t[dh].*?>(.*?)</t[dh]>", tr, re.S)]
        if cells:
            rows.append(cells)
    if len(rows) < 2:
        return []

    header, data_rows = rows[0], rows[1:]
    if len(header) < 2:
        pairs: list[tuple[str, str]] = []
        for row in data_rows:
            profile_cell = row[0].strip().replace("\xa0", "")
            if profile_cell:
                pairs.append(("", profile_cell))
        return pairs

    track_col = next(
        (i for i, name in enumerate(header) if "track" in name.lower()), 0
    )
    profile_col = next(
        (i for i, name in enumerate(header) if "profile" in name.lower()), 1 - track_col
    )
    pairs = []
    current_track = ""
    for row in data_rows:
        track_cell = (row[track_col].strip().replace("\xa0", "") if track_col < len(row) else "")
        profile_cell = (row[profile_col].strip() if profile_col < len(row) else "")
        if track_cell:
            current_track = track_cell
        if profile_cell:
            pairs.append((current_track, profile_cell))
    return pairs


def parse_labelled_items(content_html: str, item_class: str) -> list[tuple[str, str]]:
    """(label, full item text) for every `<div class="{item_class}">...</div>` block.

    The Training System, Application Conditions and Scholarship Acceptance
    sections each render as a flat list of these divs - one per fact ("Start
    Date", "Program Duration", "Training Modality", one eligibility condition,
    one application step...). Splitting on them is what turns one 1,500-character
    blob mixing four unrelated facts into four short, individually retrievable
    chunks: without this, "DEPI أونلاين ولا حضوري؟" (a question about ONE of the
    seven facts in Training System) had to match against a chunk whose embedding
    represented an average of all seven, and lost the retrieval candidate pool
    entirely (see 01_scraping/README.md, "Why item-level splitting matters").

    `label` is the item's own `<strong>` heading when it has one, else "" (the
    Application Conditions / Scholarship items have no heading - each is a
    single, already-atomic sentence or two).
    """
    # Slicing from the *end* of the opening tag (not from `class="..."` itself,
    # which sits inside it) is what keeps that tag's own markup out of the item's
    # text - starting mid-tag left a literal `class="system-item">` string as a
    # visible prefix on every single item this once produced.
    marker = re.compile(rf'<div class="{re.escape(item_class)}"[^>]*>')
    starts = [m.end() for m in marker.finditer(content_html)]
    items = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(content_html)
        block = content_html[start:end]
        label_match = re.search(r"<strong>(.*?)</strong>", block)
        label = strip_tags(label_match.group(1)) if label_match else ""
        text = strip_tags(block)
        if text:
            items.append((label, text))
    return items


def parse_track_cards(content_html: str) -> list[dict]:
    """One dict per `<div class="track-card">` block: {"title": ..., "fields": {label: text}}.

    A card's fields are whatever `<h4>label</h4>` headings it actually has -
    "Overview", "Who is this track for?", "Delivery Approach", etc. A card
    missing a heading (not every track states "Upon Completion") simply has no
    entry for it; nothing is filled in.
    """
    cards = []
    starts = [m.start() for m in re.finditer(r'<div class="track-card">', content_html)]
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(content_html)
        block = content_html[start:end]

        title_match = re.search(r'track-card-title">(.*?)</span>', block)
        title = strip_tags(title_match.group(1)) if title_match else f"Track {index + 1}"

        fields: dict[str, str] = {}
        labels = [(m.start(), m.end(), m.group(1)) for m in re.finditer(r"<h4>(.*?)</h4>", block)]
        for i, (_, label_end, label) in enumerate(labels):
            content_end = labels[i + 1][0] if i + 1 < len(labels) else len(block)
            fields[label.strip()] = strip_tags(block[label_end:content_end])
        cards.append({"title": title, "fields": fields})
    return cards


# --- fetching -------------------------------------------------------------
def fetch_page(slug: str) -> dict | None:
    """One page's data from the API, or None (logged) if it could not be fetched.

    A single missing/broken page must not lose the other pages' data - the
    caller degrades gracefully per page, never aborts the whole collection for
    one failure.
    """
    try:
        response = requests.get(
            API_URL, params={"pageUrl": slug}, headers=API_HEADERS, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as e:
        logger.warning(f"DEPI API request failed for '{slug}': {type(e).__name__}: {e}")
        return None

    if not payload.get("succeeded") or not payload.get("data"):
        logger.warning(f"DEPI API returned no data for '{slug}': {payload.get('message')}")
        return None
    return payload["data"]


def _sub_sections(data: dict) -> dict[str, dict]:
    """{stripped title: subPageContent} for one page's data - the CMS pads some
    titles with trailing whitespace/newlines ("Scholarship Acceptance Criteria\\r\\n")."""
    return {sub.get("title", "").strip(): sub for sub in (data.get("subPageContents") or [])}


def _section_text(sections: dict[str, dict], *titles: str) -> str:
    """Plain text of the first matching section title, or "" if none match.

    Multiple titles handle the one confirmed spelling inconsistency between the
    two programme pages ("Initiative Tracks" vs "Iniative Tracks").
    """
    for title in titles:
        if title in sections:
            return strip_tags(sections[title].get("content", ""))
    return ""


# --- page builders --------------------------------------------------------
# Each function returns a list of "page" dicts in the schema
# 01_scraping/collect_web_data.py already uses: org, document, page, title, url,
# source_type, text, plus whichever structured fields it already knows.
_PAGE_COUNTER = {"n": 0}


def _next_page_number() -> int:
    _PAGE_COUNTER["n"] += 1
    return _PAGE_COUNTER["n"]


def _make_page(*, title: str, url: str, text: str, category: str, categories: str,
                program: str = "", track: str = "", specialization: str = "",
                duration: str = "", duration_unit: str = "", training_type: str = "") -> dict:
    page = {
        "org": "depi",
        "document": "DEPI_Official_API",
        "page": _next_page_number(),
        "title": title,
        "url": url,
        # "web", not a bespoke full-weight value: tried "api" (exempt from
        # RETRIEVAL_WEB_SOURCE_WEIGHT's 0.7x) on the reasoning that this is DEPI's
        # own live backend, not a generic scraped page - measured on
        # 07_evaluation/test_questions.jsonl, and it cost the shared corpus real
        # accuracy (hit rate 90.3% -> 80.6%, MRR 0.71 -> 0.60): 109 new,
        # full-weight DEPI chunks crowded out ITI/NTI answers on questions that
        # name no organisation (e.g. "ما هي الأوراق المطلوبة للتقديم؟"), which
        # then compete on raw similarity alone. "web" restores the existing
        # 0.7x preference for the official PDFs/existing material and recovered
        # the suite to 87.1%/0.68. DEPI's own questions do not need the extra
        # weight - they are already found via the org + category/name boosts
        # (see retriever.py), which this value does not affect.
        "source_type": "web",
        "category": category,
        "categories": categories,
        "text": text.strip() or NOT_SPECIFIED,
    }
    for key, value in (("program", program), ("track", track), ("specialization", specialization),
                       ("duration", duration), ("duration_unit", duration_unit),
                       ("training_type", training_type)):
        if value:
            page[key] = value
    return page


def collect_organization_info() -> list[dict]:
    """Org-level pages from https://depi.gov.eg/aboutdepi: Vision, Mission, Objectives,
    Scholarship Benefits, and the one-paragraph summary of each programme."""
    data = fetch_page(ABOUT_SLUG)
    if data is None:
        return [_make_page(
            title="DEPI - About the Initiative", url=ABOUT_URL,
            text=NOT_SPECIFIED, category="organization_info", categories="organization_info",
        )]

    sections = _sub_sections(data)
    pages = []
    for title in ("Vision", "Mission", "Objectives", "Scholarship Benefits", "Depi", "Depi Industry"):
        text = _section_text(sections, title)
        pages.append(_make_page(
            title=f"DEPI - {title}", url=ABOUT_URL,
            text=text or NOT_SPECIFIED,
            category="organization_info", categories="organization_info",
        ))
    return pages


def _canonical_track(card_title: str) -> str:
    return TRACK_CARD_ALIASES.get(card_title.strip().lower(), card_title.strip())


def collect_program(slug: str) -> list[dict]:
    """Every page for one DEPI programme: tracks, specialisations, duration,
    training type, eligibility and application info.

    Nothing is skipped for being hard to parse: a section whose HTML shape
    doesn't match (a heading renamed, a table restructured) still produces a
    record for that programme, with "Not specified in source" as its text,
    rather than silently disappearing from the output.
    """
    program_name, program_url = PROGRAM_PAGES[slug]
    data = fetch_page(slug)
    if data is None:
        return [_make_page(
            title=f"{program_name} - Programme Information", url=program_url,
            text=NOT_SPECIFIED, category="programs", categories="programs",
            program=program_name,
        )]

    sections = _sub_sections(data)
    pages: list[dict] = []

    # -- tracks + specialisations, from the Track/Job-Profile table -----------
    table_html = sections.get("Initiative Tracks", sections.get("Iniative Tracks", {})).get("content", "")
    pairs = parse_table_rows(table_html)
    # DEPI Industry's table has no track column; every profile belongs to one
    # umbrella track named after the programme itself.
    pairs = [
        (_TRACK_NAME_FIXES.get(track.lower(), track) if track else program_name, profile)
        for track, profile in pairs
    ]

    tracks_to_profiles: dict[str, list[str]] = {}
    for track, profile in pairs:
        tracks_to_profiles.setdefault(track, []).append(profile)

    if not tracks_to_profiles:
        pages.append(_make_page(
            title=f"{program_name} - Tracks and Specialisations", url=program_url,
            text=NOT_SPECIFIED, category="tracks", categories="tracks,programs",
            program=program_name,
        ))
    else:
        # ONE record naming every track in this programme, with no single
        # specialisation attached. Without it, "What tracks does DEPI offer?"
        # (a question about the *list*, not about one job profile) had nothing
        # to retrieve except the per-specialisation records - each naming only
        # its own track - so five slots of six could easily land on one or two
        # tracks and never mention the rest. This card is deliberately short and
        # names nothing but the tracks, so it competes as a strong, focused match
        # for exactly this question. Arabic labels are included so "التراكات
        # الموجودة في DEPI" (a lexical/BM25 match, not just a semantic one) finds
        # it too, without touching the shared cross-lingual expansion logic.
        track_names = ", ".join(tracks_to_profiles)
        pages.append(_make_page(
            title=f"{program_name} - List of Tracks", url=program_url,
            text=(f"{program_name} tracks / التراكات المتاحة في {program_name}: "
                  f"{program_name} offers these {len(tracks_to_profiles)} technology "
                  f"tracks (specializations / مسارات): {track_names}."),
            category="tracks", categories="tracks,programs",
            program=program_name,
        ))
        for track, profiles in tracks_to_profiles.items():
            profile_list = ", ".join(profiles)
            # ONE record naming every specialisation of THIS track together, in
            # addition to the per-specialisation records below. The per-
            # specialisation records answer "tell me about job profile X"; this
            # one answers "what specializations does the Y track have" - a
            # different question, whose complete answer is scattered one name
            # per chunk otherwise. Without it, a local model asked to list a
            # track's specialisations had to correctly aggregate several sparse
            # retrieved chunks itself, which it did not reliably do (it named
            # tracks instead of the specialisations within them).
            pages.append(_make_page(
                title=f"{program_name} - {track} - All Specializations", url=program_url,
                text=(f"{program_name} - {track} track / مسار {track}: this track includes "
                      f"{len(profiles)} specializations / job profiles (تخصصات): {profile_list}."),
                category="tracks", categories="tracks,programs",
                program=program_name, track=track,
            ))
            for profile in profiles:
                pages.append(_make_page(
                    title=f"{program_name} - {track} - {profile}", url=program_url,
                    text=(f"{program_name} - {track} track includes the specialisation / "
                          f"job profile: {profile}. Other job profiles under the {track} "
                          f"track: {profile_list}."),
                    category="tracks", categories="tracks,programs",
                    program=program_name, track=track, specialization=profile,
                ))

    # -- per-track overview text (Overview / Who for / Delivery / Outcomes) ---
    cards = parse_track_cards(sections.get("Technological Tracks", {}).get("content", ""))
    # Only real track cards carry an "Overview" field; DEPI Industry's roadmap
    # cards ("2 - Soft Skills", "3 - Freelance", ...) do not and are skipped -
    # they describe programme phases, not a track, so they belong nowhere in
    # the Organization -> Program -> Track -> Specialization hierarchy.
    for card in cards:
        if "Overview" not in card["fields"]:
            continue
        track = _canonical_track(card["title"])
        if track not in tracks_to_profiles:
            # A card whose title matches none of the table's tracks (seen for
            # DEPI Industry, where each card IS a specialisation): file it under
            # that specialisation directly rather than dropping it. Matched by
            # substring, not equality - the CMS truncates one card's title
            # ("Advanced Marketing Automation with AI") relative to the table's
            # full name for the same profile ("... with AI Professional"), so an
            # exact match silently lost that one card's Overview/Who-for text.
            match = next(
                (profile for profile in tracks_to_profiles.get(program_name, [])
                 if card["title"].strip().lower() in profile.lower()
                 or profile.lower() in card["title"].strip().lower()),
                "",
            )
            track, specialization = program_name, match
        else:
            specialization = ""
        body = "\n".join(f"{label}: {text}" for label, text in card["fields"].items())
        pages.append(_make_page(
            title=f"{program_name} - {track} - Overview", url=program_url,
            text=body, category="tracks", categories="tracks,programs,eligibility",
            program=program_name, track=track, specialization=specialization,
        ))

    # -- Training System, one record per item (Start Date, Program Duration,
    # Training Schedule, Training Modality, ...) instead of one blob for the
    # whole section - see parse_labelled_items()'s docstring for why. Each
    # item's category is decided by its own label, not the section's.
    training_html = sections.get("Training System", {}).get("content", "")
    training_items = parse_labelled_items(training_html, "system-item")
    if not training_items:
        pages.append(_make_page(
            title=f"{program_name} - Training System", url=program_url,
            text=NOT_SPECIFIED, category="duration", categories="duration,training_type",
            program=program_name,
        ))
    for label, text in training_items:
        lowered = label.lower()
        if "duration" in lowered or "schedule" in lowered:
            value, unit = _extract_duration_words(text)
            pages.append(_make_page(
                title=f"{program_name} - {label}", url=program_url, text=text,
                category="duration", categories="duration,training_type,programs",
                program=program_name,
                duration=f"{value} {unit}".strip() if value else "", duration_unit=unit,
            ))
        elif "modality" in lowered:
            training_type_value = _extract_training_type_words(text)
            # A short bilingual keyword line, not a translation of the record:
            # Arabic questions about delivery mode ("DEPI أونلاين ولا حضوري؟")
            # otherwise have to cross the embedding model's English/Arabic gap
            # unaided, competing against literally-worded Arabic Q&A chunks from
            # OTHER organisations. This gives BM25 an exact Arabic term to match
            # on this org's own correct answer, without touching the shared
            # cross-lingual expansion logic other organisations also rely on.
            keywords = {
                "blended": "التدريب هجين / مدمج (أونلاين وحضوري - Hybrid: online and in-person)",
                "online": "التدريب أونلاين بالكامل (Fully online)",
                "onsite": "التدريب حضوري بالكامل (Fully in-person / onsite)",
            }.get(training_type_value, "")
            pages.append(_make_page(
                title=f"{program_name} - {label}", url=program_url,
                text=f"{text}\n{keywords}".strip(),
                category="training_type", categories="training_type,duration",
                program=program_name, training_type=training_type_value,
            ))
        elif "start date" in lowered:
            pages.append(_make_page(
                title=f"{program_name} - {label}", url=program_url, text=text,
                category="application", categories="application",
                program=program_name,
            ))
        else:
            # Language of Instruction, Participation and Obligations, Certification:
            # real information, but not one of the categories retrieval prioritises
            # by name. Filed as "programs" so it is still findable, not dropped.
            pages.append(_make_page(
                title=f"{program_name} - {label or 'Training System'}", url=program_url,
                text=text, category="programs", categories="programs,eligibility",
                program=program_name,
            ))

    # -- Application Conditions, one record per eligibility condition -----------
    conditions = parse_labelled_items(
        sections.get("Application Conditions", {}).get("content", ""), "official-item"
    )
    if not conditions:
        pages.append(_make_page(
            title=f"{program_name} - Eligibility Conditions", url=program_url,
            text=NOT_SPECIFIED, category="eligibility", categories="eligibility,application",
            program=program_name,
        ))
    for _, text in conditions:
        pages.append(_make_page(
            title=f"{program_name} - Eligibility Condition", url=program_url, text=text,
            category="eligibility", categories="eligibility,application",
            program=program_name,
        ))

    # -- Scholarship Acceptance Criteria, one record per application step -------
    steps = parse_labelled_items(
        sections.get("Scholarship Acceptance Criteria",
                     sections.get("Scholarship Acceptance Criteria\r\n", {})).get("content", ""),
        "official-item",
    )
    if not steps:
        pages.append(_make_page(
            title=f"{program_name} - How to Apply", url=program_url,
            text=NOT_SPECIFIED, category="application", categories="application,eligibility",
            program=program_name,
        ))
    for _, text in steps:
        pages.append(_make_page(
            title=f"{program_name} - Application Step", url=program_url, text=text,
            category="application", categories="application,eligibility",
            program=program_name,
        ))

    # -- education requirements per college, when the source states them --------
    college_section = sections.get("Program Available For each College")
    if college_section and college_section.get("accordions"):
        for accordion in college_section["accordions"]:
            college = accordion.get("title", "").strip()
            rows = parse_table_rows(accordion.get("content", ""))
            if not college or not rows:
                continue
            profiles = ", ".join(sorted({profile for _, profile in rows}))
            pages.append(_make_page(
                title=f"{program_name} - Eligible Job Profiles for {college}", url=program_url,
                text=(f"Students/graduates of {college} in {program_name} are eligible to "
                      f"apply for these job profiles: {profiles}."),
                category="eligibility", categories="eligibility,application",
                program=program_name,
            ))

    return pages


# --- small text-based extractors, scoped to this module's own prose -----------
# These intentionally do NOT reuse 03_rag_pipeline/preprocessing/structure.py's
# extract_duration()/extract_training_type(): those are tuned for numeric-digit
# patterns in the PDF catalogues ("TOTAL HOURS 1,180hrs"), while DEPI's own API
# text states duration in words ("Six months") and delivery as a named system
# ("Hybrid system: 75% online and 25% in-person"). Keeping this parsing local to
# depi_api.py, rather than editing the shared module, is what keeps this fix
# scoped to DEPI only.
_WORD_NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
                 "seven": 7, "eight": 8, "nine": 9, "ten": 11, "eleven": 11, "twelve": 12}


def _extract_duration_words(text: str) -> tuple[str, str]:
    """("6", "months") from "Program Duration Six months, comprising...", or ("", "")."""
    match = re.search(
        r"Program Duration:?\s*(\w+)\s+(month|week|hour)s?", text or "", re.I
    )
    if not match:
        return "", ""
    word, unit = match.group(1).lower(), match.group(2).lower() + "s"
    if word.isdigit():
        return word, unit
    return (str(_WORD_NUMBERS[word]), unit) if word in _WORD_NUMBERS else ("", "")


def _extract_training_type_words(text: str) -> str:
    """"blended" from "Hybrid system: 75% online and 25% in-person...", else ""."""
    lowered = (text or "").lower()
    if "hybrid" in lowered or ("online" in lowered and ("in-person" in lowered or "onsite" in lowered)):
        return "blended"
    if "online" in lowered:
        return "online"
    if "in-person" in lowered or "onsite" in lowered or "on-site" in lowered:
        return "onsite"
    return ""


# --- the one entry point collect_web_data.py calls -----------------------------
def collect_depi_pages() -> list[dict]:
    """Every DEPI page this module can produce: org info + both programmes.

    Never raises for a single missing section - see `fetch_page` and the
    per-section fallbacks in `collect_program`. Returns an empty list only if
    the API is unreachable for every single page, which the caller treats as a
    hard failure (same contract as `collect_web_data.collect_data`).
    """
    pages = collect_organization_info()
    for slug in PROGRAM_PAGES:
        pages.extend(collect_program(slug))
    return pages


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    result = collect_depi_pages()
    print(f"Collected {len(result)} DEPI pages from the live API.")
    by_category: dict[str, int] = {}
    for page in result:
        by_category[page["category"]] = by_category.get(page["category"], 0) + 1
    for category, count in sorted(by_category.items()):
        print(f"  {category:<18} {count}")
