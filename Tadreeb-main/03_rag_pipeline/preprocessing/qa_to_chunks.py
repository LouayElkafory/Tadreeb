"""
Preprocessing step 4: turn the curated Q&A pairs into retrievable chunks.
Reads 02_data/02_qa_pairs/<org>_qa.jsonl -> writes 02_data/04_chunks/qa_chunks.jsonl

These pairs already existed as fine-tuning data but were never indexed, which
left a real gap: the document corpus is almost entirely English PDF text while
users ask in Egyptian Arabic, so Arabic questions had very little Arabic content
to match against. The pairs are curated from the same official sources and are
phrased the way users actually ask, so indexing them raises Arabic recall
sharply. Both question and answer go into the chunk - the question half is what
matches the user's phrasing, the answer half is what grounds the reply.

qa_dataset.jsonl is skipped on purpose: it is the concatenation of the per-org
files, and indexing it too would duplicate every pair.
"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
QA_FOLDER = PROJECT_ROOT / "02_data" / "02_qa_pairs"
CHUNKS_FOLDER = PROJECT_ROOT / "02_data" / "04_chunks"

ORG_TITLES = {
    "depi": "أسئلة وأجوبة DEPI",
    "iti": "أسئلة وأجوبة ITI",
    "nti": "أسئلة وأجوبة NTI",
    "itida": "أسئلة وأجوبة ITIDA",
}


def qa_to_chunk(pair: dict, org: str, page: int) -> dict:
    """One Q&A pair as a self-contained chunk."""
    return {
        "org": org,
        "document": f"{org}_qa.jsonl",
        "title": ORG_TITLES.get(org, f"{org.upper()} Q&A"),
        "page": page,
        "source_type": "qa",
        "text": f"س: {pair['instruction'].strip()}\nج: {pair['response'].strip()}",
    }


def build_chunks() -> list[dict]:
    chunks = []
    seen = set()
    for qa_file in sorted(QA_FOLDER.glob("*_qa.jsonl")):
        org = qa_file.stem.replace("_qa", "")
        with open(qa_file, "r", encoding="utf-8") as f:
            pairs = [json.loads(line) for line in f if line.strip()]
        for pair in pairs:
            question = pair.get("instruction", "").strip()
            answer = pair.get("response", "").strip()
            if not question or not answer or question in seen:
                continue
            seen.add(question)
            chunks.append(qa_to_chunk(pair, org, len(chunks) + 1))
    return chunks


if __name__ == "__main__":
    CHUNKS_FOLDER.mkdir(parents=True, exist_ok=True)
    chunks = build_chunks()
    output_path = CHUNKS_FOLDER / "qa_chunks.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"Wrote {len(chunks)} Q&A chunks -> {output_path}")
