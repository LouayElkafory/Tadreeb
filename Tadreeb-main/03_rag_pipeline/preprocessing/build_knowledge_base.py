"""
Preprocessing step 5: assemble the structured knowledge base.

    python 03_rag_pipeline/preprocessing/build_knowledge_base.py

Reads every `02_data/04_chunks/*_chunks.jsonl` and produces two things:

1. `02_data/05_structured/<org>_knowledge.json` - the explicit hierarchy, so the
   relationship between an organisation, its programs and their tracks is stored
   rather than implied:

       ITI
        └── Professional Training Program
             ├── Data Science      : 1,455 hours, blended
             └── Data Management   : 1,180 hours, blended

   This file is the inspectable artifact - open it to see exactly what the system
   believes about each organisation, and where each fact came from.

2. `02_data/04_chunks/<org>_structured_chunks.jsonl` - one short "fact card" per
   track, which then gets embedded alongside everything else.

Why the fact cards matter: the facts that answer "مدة تراك Data Science في ITI قد
إيه؟" are spread across a brochure - the track is named on page 1, the hours are
in a table on page 3. Neither page answers the question on its own, and a
retriever can only return whole chunks. A card collects the extracted values for
one track into a single short chunk that does answer it.

Nothing on a card is invented. Every line is either a value `structure.py`
extracted from the source text, or a verbatim excerpt of that text. A track whose
duration the documents never state simply has no duration line.

This step is additive: it writes new files and touches none of the existing ones.
Re-run it after `chunker.py`/`qa_to_chunks.py`, then run `embed_and_store.py` (or
`backfill_structure.py`) to get the cards into the vector DB.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from structure import document_profiles, enrich  # noqa: E402

CHUNKS_FOLDER = PROJECT_ROOT / "02_data" / "04_chunks"
STRUCTURED_FOLDER = PROJECT_ROOT / "02_data" / "05_structured"

ORG_NAMES = {
    "iti": "ITI (Information Technology Institute)",
    "nti": "NTI (National Telecommunication Institute)",
    "depi": "DEPI (Digital Egypt Pioneers Initiative)",
    "itida": "ITIDA (IT Industry Development Agency)",
}

# A small, source-bound correction for one page shape that the generic chunker
# cannot preserve. NTI's official Private Summer Training page lists these six
# headings in one long numbered block. The sliding chunks split several headings
# from their surrounding text, so only two can be recovered by `extract_track`.
# These are not inferred recommendations: each name and both durations are stated
# on that official page, which is retained as the source URL on every card. The
# programme and its tracks have DIFFERENT durations there - the programme is 4
# weeks / 120 hours (30 soft-skills + 90 technical); each track is the 90-hour
# technical part. Using one "90 hours" for both made the chatbot answer "the
# summer training is 90 hours", which understates the programme by 30 hours.
OFFICIAL_TRACK_OVERRIDES = {
    "nti": {
        "Private Summer Training": {
            "source": "NTI Private Summer Training Tracks",
            "url": "https://nti.sci.eg/prisummer/tracks.php",
            "program_duration": "120 hours over 4 weeks (30 hours soft skills + 90 hours technical training)",
            "track_duration": "90 hours of technical training (part of the 120-hour, 4-week programme)",
            "tracks": (
                "Telecom Engineering",
                "System Engineering",
                "Software Engineering",
                "Network Engineering",
                "Data Engineering",
                "Electronics and Embedded Systems",
            ),
        },
    },
}

# Cards are only worth making for a track we can say something concrete about.
CARD_FIELDS = ("program", "duration", "training_type", "specialization")
DESCRIPTION_LIMIT = 320


def load_chunks() -> list[dict]:
    """Every chunk in the corpus, excluding the cards from a previous run."""
    chunks = []
    for path in sorted(CHUNKS_FOLDER.glob("*_chunks.jsonl")):
        if path.name.endswith("_structured_chunks.jsonl"):
            continue
        with open(path, "r", encoding="utf-8") as f:
            chunks.extend(json.loads(line) for line in f if line.strip())
    return chunks


def structured_records(chunks: list[dict]) -> list[dict]:
    """Every chunk with its structured metadata attached."""
    profiles = document_profiles(chunks)
    records = []
    for chunk in chunks:
        key = (chunk.get("org", ""), chunk.get("document", ""))
        records.append({**chunk, **enrich(chunk, profiles.get(key))})
    return records


# A table-of-contents page is mostly dotted leaders and page numbers. It mentions
# every track in the catalogue, so it otherwise wins the "describes this track"
# contest for all of them and puts "Contents Introduction ......... 4" on 6 cards.
_TOC = re.compile(r"\.{4,}")
_PROSE = re.compile(r"[A-Za-zء-ي]{3,}")


_LEADING_PAGE_NUMBER = re.compile(r"^\d{1,3}\s+")
# Scraped pages carry a login/cookie banner that mentions the page title, so it
# otherwise scores as the best description of it.
_NAVIGATION = (
    "log in", "login", "skip to main content", "privacy policy", "sign up",
    "searching is not enabled", "turn on more accessible", "cookie",
)


def _readable_score(text: str, name: str, record: dict) -> tuple:
    """Rank candidate excerpts: prose that names the subject and starts a sentence."""
    digits = sum(c.isdigit() for c in text)
    first = text[:1]
    return (
        bool(_TOC.search(text)),                     # table of contents last
        digits / max(len(text), 1) > 0.15,           # mostly a numbers table
        name.lower() not in text.lower(),            # does it actually name it
        sum(marker in text.lower() for marker in _NAVIGATION) >= 2,  # nav furniture
        record.get("source_type") == "qa",           # a Q&A answer is not a description
        first.islower(),                             # starts mid-sentence
        -len(_PROSE.findall(text)),                  # prefer real sentences
    )


def _first_description(records: list[dict], name: str) -> str:
    """A verbatim excerpt introducing the track/program, for the description line."""
    candidates = []
    for record in records:
        text = " ".join((record.get("text") or "").split())
        # PDF pages open with their own page number: "26 AI & DATA SCIENCE TRACK ...".
        text = _LEADING_PAGE_NUMBER.sub("", text)
        if len(text) >= 80:
            candidates.append((_readable_score(text, name, record), record.get("page") or 0, text))
    if not candidates:
        return ""
    candidates.sort(key=lambda c: (c[0], c[1]))
    text = candidates[0][2]
    if len(text) <= DESCRIPTION_LIMIT:
        return text
    # Cut on a sentence boundary so the excerpt does not end mid-word.
    cut = text[:DESCRIPTION_LIMIT]
    stop = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    return (cut[: stop + 1] if stop > DESCRIPTION_LIMIT // 2 else cut.rstrip() + "...")


def _dedupe_names(names) -> list[str]:
    """Sorted unique names, dropping ones that merely extend a shorter entry.

    A profile name with no following item number gets cut by the 50-character
    capture limit and comes back duplicated ("Fortinet Cybersecurity Engineer
    Fortinet Cybersecur"); keeping the shorter, clean form drops it.
    """
    unique = sorted({n.strip() for n in names if n and n.strip()}, key=lambda n: (len(n), n))
    kept: list[str] = []
    for name in unique:
        if not any(name.lower().startswith(k.lower()) for k in kept):
            kept.append(name)
    return sorted(kept)


def build_tree(records: list[dict]) -> dict[str, dict]:
    """org -> {programs -> tracks -> facts}, plus where each fact came from."""
    tree: dict[str, dict] = {}
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)

    for record in records:
        org = record.get("org", "")
        if not org:
            continue
        node = tree.setdefault(org, {
            "organization": org.upper(),
            "organization_name": ORG_NAMES.get(org, org.upper()),
            "official_website": "",
            "programs": {},
            "tracks": {},
            "categories": {},
        })
        node["categories"][record.get("category", "general")] = (
            node["categories"].get(record.get("category", "general"), 0) + 1
        )
        if not node["official_website"] and record.get("url"):
            node["official_website"] = record["url"]

        program = record.get("program")
        if program:
            node["programs"].setdefault(program, {"tracks": [], "sources": set()})
            node["programs"][program]["sources"].add(record.get("document", ""))

        track = record.get("track")
        if track:
            grouped[(org, track)].append(record)

    for (org, track), track_records in grouped.items():
        node = tree[org]
        facts: dict[str, object] = {"track": track}
        for field in CARD_FIELDS:
            value = next((r[field] for r in track_records if r.get(field)), "")
            if value:
                facts[field] = value
        # Every job profile listed under this track, not just the first. This is
        # what answers "إيه التخصصات الموجودة في DEPI؟" - DEPI's tracks state no
        # duration of their own, but they do list their specialisations.
        specializations = _dedupe_names(
            name
            for record in track_records
            for name in (record.get("specializations") or
                         ([record["specialization"]] if record.get("specialization") else []))
        )
        if specializations:
            facts["specializations"] = specializations
        facts["description"] = _first_description(track_records, track)
        facts["sources"] = sorted({r.get("document", "") for r in track_records if r.get("document")})
        urls = sorted({r["url"] for r in track_records if r.get("url")})
        if urls:
            facts["source_url"] = urls[0]
        node["tracks"][track] = facts

        program = facts.get("program")
        if program and track not in node["programs"].setdefault(
            program, {"tracks": [], "sources": set()}
        )["tracks"]:
            node["programs"][program]["tracks"].append(track)

    # Program-level facts, for organisations whose material is organised by
    # program rather than by track - NTI states "Train To Hire (4 Month)" and
    # never uses the word "track" at all, so without this it would get no card.
    by_program: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for record in records:
        if record.get("org") and record.get("program"):
            by_program[(record["org"], record["program"])].append(record)
    for (org, program), program_records in by_program.items():
        entry = tree[org]["programs"].setdefault(program, {"tracks": [], "sources": set()})
        for field in ("duration", "duration_unit", "training_type"):
            value = next((r[field] for r in program_records if r.get(field)), "")
            if value and field not in entry:
                entry[field] = value
        entry["description"] = _first_description(program_records, program)
        urls = sorted({r["url"] for r in program_records if r.get("url")})
        if urls:
            entry["source_url"] = urls[0]

    # See OFFICIAL_TRACK_OVERRIDES above. This only fills track headings that
    # the named official source explicitly states; it never derives a track
    # from another institution or from model output.
    for org, programs in OFFICIAL_TRACK_OVERRIDES.items():
        node = tree.get(org)
        if not node:
            continue
        for program, details in programs.items():
            program_entry = node["programs"].setdefault(program, {"tracks": [], "sources": set()})
            program_entry["duration"] = details["program_duration"]
            program_entry["duration_unit"] = "hours"
            program_entry["source_url"] = details["url"]
            program_entry["sources"].add(details["source"])
            for track in details["tracks"]:
                node["tracks"].setdefault(track, {
                    "track": track,
                    "program": program,
                    "duration": details["track_duration"],
                    "duration_unit": "hours",
                    "sources": [details["source"]],
                    "source_url": details["url"],
                })
                if track not in program_entry["tracks"]:
                    program_entry["tracks"].append(track)

    # Sets are not JSON-serialisable, and sorted output keeps the file diffable.
    for node in tree.values():
        node["programs"] = {
            name: {**{k: v for k, v in data.items() if k not in ("tracks", "sources")},
                   "tracks": sorted(data["tracks"]),
                   "sources": sorted(s for s in data["sources"] if s)}
            for name, data in sorted(node["programs"].items())
        }
        node["tracks"] = dict(sorted(node["tracks"].items()))
    return tree


def card_text(org: str, name: str, kind: str, facts: dict) -> str:
    """The fact card, in the order a reader would want it. Only stated values.

    Every line is either an extracted value or a verbatim excerpt. A field the
    documents never state is absent, not guessed - which is why the answer to
    "how long is track X" can honestly be "the sources don't say".
    """
    lines = [
        f"{org.upper()} - {name} {kind}",
        f"Organization: {ORG_NAMES.get(org, org.upper())}",
    ]
    if kind == "track" and facts.get("program"):
        lines.append(f"Program: {facts['program']}")
    lines.append(f"{kind.capitalize()}: {name}")
    if facts.get("tracks"):
        lines.append(f"Tracks in this program: {', '.join(facts['tracks'])}")
    if facts.get("specializations"):
        lines.append(f"Specializations / job profiles: {', '.join(facts['specializations'])}")
    if facts.get("duration"):
        lines.append(f"Training duration: {facts['duration']}")
    if facts.get("training_type"):
        lines.append(f"Training type / delivery mode: {facts['training_type']}")
    if facts.get("description"):
        lines.append(f"About: {facts['description']}")
    sources = facts.get("sources") or []
    if sources:
        lines.append(f"Source document: {', '.join(sources[:3])}")
    if facts.get("source_url"):
        lines.append(f"Source URL: {facts['source_url']}")
    return "\n".join(lines)


# A card only earns its place if it states something the reader asked about. A
# card holding nothing but a name would just repeat what the corpus already says,
# while competing with it in retrieval.
_CARD_WORTH_INDEXING = ("duration", "training_type", "program", "specializations", "tracks")
_CARD_METADATA = ("program", "duration", "duration_unit", "training_type")


def build_cards(tree: dict[str, dict]) -> dict[str, list[dict]]:
    """org -> the fact-card chunks to index, for each program and each track."""
    cards: dict[str, list[dict]] = {}
    for org, node in tree.items():
        org_cards: list[dict] = []

        def add(name: str, kind: str, facts: dict) -> None:
            if not any(facts.get(field) for field in _CARD_WORTH_INDEXING):
                return
            card = {
                "org": org,
                "document": f"{org.upper()}_Structured_Knowledge_Base",
                "page": len(org_cards) + 1,
                "title": f"{org.upper()} {name} {kind} - key facts",
                "source_type": "structured",
                "category": "duration" if facts.get("duration") else "tracks",
                "categories": "tracks,programs,duration,training_type,organization_info",
                kind: name,
                "text": card_text(org, name, kind, facts),
            }
            for field in _CARD_METADATA:
                if facts.get(field):
                    card[field] = facts[field]
            if facts.get("source_url"):
                card["url"] = facts["source_url"]
            org_cards.append(card)

        for program, facts in node["programs"].items():
            add(program, "program", facts)
        for track, facts in node["tracks"].items():
            add(track, "track", facts)

        if org_cards:
            cards[org] = org_cards
    return cards


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    chunks = load_chunks()
    if not chunks:
        print(f"No chunks in {CHUNKS_FOLDER}. Run chunker.py first.")
        return 1
    print(f"Reading {len(chunks)} chunks...")

    records = structured_records(chunks)
    tree = build_tree(records)

    STRUCTURED_FOLDER.mkdir(parents=True, exist_ok=True)
    cards = build_cards(tree)

    for org, node in sorted(tree.items()):
        output = STRUCTURED_FOLDER / f"{org}_knowledge.json"
        with open(output, "w", encoding="utf-8") as f:
            json.dump(node, f, ensure_ascii=False, indent=2)
        print(f"  {org.upper():<6} {len(node['programs'])} programs, {len(node['tracks'])} tracks, "
              f"{len(cards.get(org, []))} fact cards -> {output.relative_to(PROJECT_ROOT)}")

    for org, org_cards in sorted(cards.items()):
        output = CHUNKS_FOLDER / f"{org}_structured_chunks.jsonl"
        with open(output, "w", encoding="utf-8") as f:
            for card in org_cards:
                f.write(json.dumps(card, ensure_ascii=False) + "\n")

    total_cards = sum(len(c) for c in cards.values())
    print(f"\nWrote {total_cards} fact cards into 02_data/04_chunks/*_structured_chunks.jsonl")
    print("Run 03_rag_pipeline/embeddings/backfill_structure.py to add them to the vector DB.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
