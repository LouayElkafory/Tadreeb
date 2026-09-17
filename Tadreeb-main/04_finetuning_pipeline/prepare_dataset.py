"""
Merge the raw Q&A CSVs in 02_data/02_qa_pairs/ into per-org instruction/response
JSONL files, plus one combined dataset used for training.
"""
import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QA_FOLDER = PROJECT_ROOT / "02_data" / "02_qa_pairs"
COMBINED_DATASET_PATH = QA_FOLDER / "qa_dataset.jsonl"


# maps a source CSV filename to the org it belongs to
CSV_TO_ORG = {
    "depi_qa_dataset.csv": "depi",
    "depi_round3_qa_dataset.csv": "depi",
    "iti_ebrochure_qa_dataset.csv": "iti",
    "nti_upskilling_qa.csv": "nti",
    "itida_summer_training_qa.csv": "itida",
}


def read_qa_csv(csv_path: Path) -> list[dict]:
    pairs = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            question = row.get("question", "").strip()
            answer = row.get("answer", "").strip()
            if question and answer:
                pairs.append({"instruction": question, "response": answer})
    return pairs


def build_qa_dataset(qa_folder: str = QA_FOLDER, combined_output: str = COMBINED_DATASET_PATH) -> None:
    pairs_by_org: dict[str, list[dict]] = {}

    for csv_file in sorted(Path(qa_folder).glob("*.csv")):
        org = CSV_TO_ORG.get(csv_file.name)
        if org is None:
            continue
        pairs_by_org.setdefault(org, []).extend(read_qa_csv(csv_file))

    all_pairs = []
    for org, pairs in pairs_by_org.items():
        org_path = Path(qa_folder) / f"{org}_qa.jsonl"
        with open(org_path, "w", encoding="utf-8") as f:
            for pair in pairs:
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")
        print(f"Wrote {len(pairs)} pairs -> {org_path}")
        all_pairs.extend(pairs)

    with open(combined_output, "w", encoding="utf-8") as f:
        for pair in all_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
    print(f"Wrote {len(all_pairs)} pairs -> {combined_output}")


if __name__ == "__main__":
    build_qa_dataset()
