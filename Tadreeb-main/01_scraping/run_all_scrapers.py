"""
Orchestrates the full data ingestion pipeline:
1. Web Scraping (ITI, NTI, DEPI, ITIDA)
2. Text Cleaning (clean_text.py)
3. Deduplication (deduplicate.py)
4. Chunking (chunker.py)
5. Vector DB Embedding & ChromaDB Upsert (embed_and_store.py)
"""
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

from scrape_iti import scrape_iti
from scrape_nti import scrape_nti
from scrape_depi import scrape_depi
from scrape_itida import scrape_itida


def run_command(script_path: Path):
    print(f"\n---> Running: {script_path.relative_to(PROJECT_ROOT)}")
    res = subprocess.run([sys.executable, str(script_path)], cwd=str(PROJECT_ROOT))
    if res.returncode != 0:
        print(f"Warning: {script_path.name} exited with code {res.returncode}")


def main():
    print("=========================================")
    print("🚀 STEP 1: Running Web Scrapers...")
    print("=========================================")
    scrape_iti()
    scrape_nti()
    scrape_depi()
    scrape_itida()

    print("\n=========================================")
    print("📄 STEP 1b: Extracting Official PDFs...")
    print("=========================================")
    run_command(PROJECT_ROOT / "01_scraping" / "pdf_extractor.py")

    print("\n=========================================")
    print("🧹 STEP 2: Running Data Cleaning...")
    print("=========================================")

    run_command(PROJECT_ROOT / "03_rag_pipeline" / "preprocessing" / "clean_text.py")

    print("\n=========================================")
    print("🔍 STEP 3: Running Deduplication...")
    print("=========================================")
    run_command(PROJECT_ROOT / "03_rag_pipeline" / "preprocessing" / "deduplicate.py")

    print("\n=========================================")
    print("✂️ STEP 4: Running Text Chunking...")
    print("=========================================")
    run_command(PROJECT_ROOT / "03_rag_pipeline" / "preprocessing" / "chunker.py")

    print("\n=========================================")
    print("🧠 STEP 5: Embedding & Updating Vector DB...")
    print("=========================================")
    run_command(PROJECT_ROOT / "03_rag_pipeline" / "embeddings" / "embed_and_store.py")

    print("\n✅ Full scraping and ingestion pipeline completed successfully!")


if __name__ == "__main__":
    main()
