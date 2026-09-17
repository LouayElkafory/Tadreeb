"""
Complete Faiss RAG Pipeline for Testing
Replaces ChromaDB with Faiss, uses Ollama for local embeddings
"""
import json
import re
import numpy as np
import faiss
import ollama
from pathlib import Path
from typing import Optional

# ============================================================================
# CONFIGURATION
# ============================================================================

EMBEDDING_MODEL = "nomic-embed-text"  # Use Ollama local model
CHUNK_SIZE = 900
OVERLAP = 150
MIN_CHUNK_SIZE = 100
MIN_RETRIEVAL_SCORE = 0.30  # Lower threshold for Ollama embeddings


# ============================================================================
# 1. PDF EXTRACTION & CLEANING
# ============================================================================

def extract_pdf_text(pdf_path: Path) -> list[dict]:
    """Extract text from PDF using PyMuPDF."""
    import pymupdf

    pdf_doc = pymupdf.open(pdf_path)
    pages = []

    for page_num in range(pdf_doc.page_count):
        page = pdf_doc[page_num]
        text = page.get_text()
        pages.append({
            "page": page_num + 1,
            "text": text,
            "org": "nti",
            "document": pdf_path.name
        })

    return pages


def clean_text(text: str) -> str:
    """Remove extraction artifacts."""
    text = text.replace("\x00", " ").replace("(cid:127)", "•")
    text = re.sub(r"[\u200b\ufeff]", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def clean_pages(pages: list[dict]) -> list[dict]:
    """Filter and clean pages."""
    cleaned = []
    for page in pages:
        text = clean_text(page["text"])
        if len(text) >= 40:
            cleaned.append({**page, "text": text})
    return cleaned


# ============================================================================
# 2. TEXT CHUNKING (Overlapping + Sentence-Aware)
# ============================================================================

def split_into_units(text: str) -> list[str]:
    """Split into logical units (paragraphs/sentences)."""
    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]

    units = []
    for paragraph in paragraphs:
        parts = re.split(r"(?<=[.!?؟؛])\s+", paragraph)
        units.extend(part.strip() for part in parts if part.strip())

    return units or [text.strip()]


def split_long_unit(unit: str, chunk_size: int) -> list[str]:
    """Split very long units by word boundaries."""
    pieces = []
    remaining = unit
    while len(remaining) > chunk_size:
        cut = remaining.rfind(" ", 0, chunk_size + 1)
        cut = cut if cut >= chunk_size // 2 else chunk_size
        pieces.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        pieces.append(remaining)
    return pieces


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """Create overlapping chunks."""
    chunks = []
    current = ""

    for unit in split_into_units(text):
        for part in split_long_unit(unit, chunk_size):
            candidate = f"{current} {part}".strip() if current else part

            if current and len(candidate) > chunk_size:
                if len(current) >= MIN_CHUNK_SIZE:
                    chunks.append(current)
                overlap_text = current[-overlap:].split(" ", 1)
                overlap_text = overlap_text[-1] if len(overlap_text) == 2 else current[-overlap:]
                current = f"{overlap_text} {part}".strip()
            else:
                current = candidate

    if len(current) >= MIN_CHUNK_SIZE:
        chunks.append(current)

    return chunks


def chunk_pages(pages: list[dict]) -> list[dict]:
    """Convert pages to chunks."""
    all_chunks = []
    for page in pages:
        for index, piece in enumerate(chunk_text(page["text"])):
            all_chunks.append({
                "org": page["org"],
                "document": page["document"],
                "page": page["page"],
                "chunk_index": index,
                "text": piece,
            })
    return all_chunks


# ============================================================================
# 3. EMBEDDINGS & FAISS INDEX
# ============================================================================

class FaissRAG:
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """Initialize embedding model and Faiss index."""
        print(f"Using embedding model: {model_name} (via Ollama)")
        self.model_name = model_name
        self.index = None
        self.chunks = None
        self.embeddings = None
        self.embedding_dim = 384  # nomic-embed-text dimension

    def _embed_text(self, text: str) -> np.ndarray:
        """Generate embedding using Ollama."""
        response = ollama.embeddings(model=self.model_name, prompt=text)
        return np.array(response["embedding"])

    def add_chunks(self, chunks: list[dict]) -> None:
        """Generate embeddings and build Faiss index."""
        self.chunks = chunks

        # Generate embeddings using Ollama
        print(f"Generating embeddings for {len(chunks)} chunks using Ollama...")
        embeddings_list = []
        for i, chunk in enumerate(chunks):
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{len(chunks)}")
            emb = self._embed_text(chunk["text"])
            embeddings_list.append(emb)

        self.embeddings = np.array(embeddings_list).astype('float32')

        # Build Faiss index
        dimension = self.embeddings.shape[1]
        self.embedding_dim = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(self.embeddings)

        print(f"✓ Faiss index created: {self.index.ntotal} vectors, {dimension} dimensions")

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        """Retrieve top-k similar chunks."""
        if self.index is None or self.chunks is None:
            return []

        # Encode query
        query_embedding = self._embed_text(query).astype('float32')
        query_embedding = np.array([query_embedding])

        # Search
        distances, indices = self.index.search(query_embedding, top_k)

        results = []
        for idx, distance in zip(indices[0], distances[0]):
            chunk = self.chunks[idx]
            # Convert L2 distance to similarity score
            similarity = 1.0 / (1.0 + distance)

            results.append({
                "text": chunk["text"],
                "score": float(similarity),
                "distance": float(distance),
                "metadata": {
                    "org": chunk["org"],
                    "document": chunk["document"],
                    "page": chunk["page"],
                    "chunk_index": chunk["chunk_index"]
                }
            })

        return results

    def save_index(self, index_path: str, chunks_path: str) -> None:
        """Save Faiss index and chunks metadata."""
        faiss.write_index(self.index, index_path)
        with open(chunks_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        print(f"✓ Saved index to {index_path}")
        print(f"✓ Saved chunks to {chunks_path}")

    def load_index(self, index_path: str, chunks_path: str) -> None:
        """Load Faiss index and chunks metadata."""
        self.index = faiss.read_index(index_path)
        with open(chunks_path, 'r', encoding='utf-8') as f:
            self.chunks = json.load(f)
        print(f"✓ Loaded index from {index_path}")
        print(f"✓ Loaded {len(self.chunks)} chunks")


# ============================================================================
# 4. TESTING & SETUP
# ============================================================================

def setup_faiss_rag(pdf_path: str) -> FaissRAG:
    """Complete setup: extract, chunk, embed, index."""
    pdf_path = Path(pdf_path)

    print("\n" + "="*80)
    print("STEP 1: Extract Text from PDF")
    print("="*80)
    pages = extract_pdf_text(pdf_path)
    print(f"✓ Extracted {len(pages)} pages")

    print("\n" + "="*80)
    print("STEP 2: Clean Text")
    print("="*80)
    cleaned_pages = clean_pages(pages)
    print(f"✓ Cleaned {len(cleaned_pages)} pages")

    print("\n" + "="*80)
    print("STEP 3: Chunk Text")
    print("="*80)
    chunks = chunk_pages(cleaned_pages)
    print(f"✓ Created {len(chunks)} chunks")
    print(f"  - Chunk size: {CHUNK_SIZE} chars")
    print(f"  - Overlap: {OVERLAP} chars")
    avg_size = np.mean([len(c['text']) for c in chunks])
    print(f"  - Avg chunk size: {avg_size:.0f} chars")

    print("\n" + "="*80)
    print("STEP 4: Generate Embeddings & Build Faiss Index")
    print("="*80)
    rag = FaissRAG()
    rag.add_chunks(chunks)

    return rag


# ============================================================================
# 5. END-TO-END TEST
# ============================================================================

def test_retrieval(rag: FaissRAG):
    """Test retrieval with sample queries."""
    test_queries = [
        "What is the HireReady program?",
        "What are the eligibility criteria?",
        "ما هي متطلبات البرنامج؟",
    ]

    print("\n" + "="*80)
    print("RETRIEVAL TEST: Expecting 3 chunks per query")
    print("="*80)

    for query in test_queries:
        print(f"\n{'─'*80}")
        print(f"Query: {query}")
        print(f"{'─'*80}")

        results = rag.retrieve(query, top_k=3)

        print(f"Retrieved {len(results)} chunks:")
        for i, result in enumerate(results, 1):
            print(f"\n[Chunk {i}] | Page {result['metadata']['page']} | Similarity: {result['score']:.4f}")
            print(f"Text: {result['text'][:150]}...")

    return True


if __name__ == "__main__":
    # Setup
    pdf_path = "D:/project/Tadreeb-main/Tadreeb-main/Tadreeb-updated-tadreeb (1)/Tadreeb-updated-tadreeb/Tadreeb-main/02_data/01_raw/nti/official/NTI_HireReady_Program_Guidelines.pdf"

    rag = setup_faiss_rag(pdf_path)

    # Test
    test_retrieval(rag)

    # Save
    rag.save_index("./faiss_hireready.index", "./chunks_metadata.json")

    print("\n" + "="*80)
    print("✅ SETUP COMPLETE - Ready for Backend Integration")
    print("="*80)
