# RAG Pipeline

A production-ready Retrieval-Augmented Generation (RAG) pipeline with multilingual support (English and Arabic).

## Architecture

```
PDF Files
   ↓
Extract Text (PyMuPDF + PyPDF fallback)
   ↓
Clean Text (remove artifacts, normalize)
   ↓
Overlapping Chunking (900 chars, 150 overlap)
   ↓
Generate Embeddings (paraphrase-multilingual-MiniLM-L12-v2)
   ↓
Index with FAISS (IndexFlatL2 - L2 distance)
   ↓
Retrieve & Rank by Similarity
```

## Components

### 1. PDF Extractor (`pdf_extractor.py`)
- **Primary**: PyMuPDF (fitz) - faster, better layout handling
- **Fallback**: PyPDF - pure Python, no system dependencies
- **Text Cleaning**: Removes null bytes, PDF markers, zero-width characters, normalizes whitespace
- **Multilingual**: Supports English and Arabic

**Usage:**
```python
from pdf_extractor import extract_pdf

pages = extract_pdf("document.pdf")
# Returns: [{"page": 1, "text": "...", "extractor": "pymupdf"}, ...]
```

### 2. Text Chunking (`chunking.py`)
- **Chunk Size**: 900 characters (default, configurable)
- **Overlap**: 150 characters (preserves context across chunks)
- **Minimum Chunk**: 100 characters (skips tiny fragments)
- **Strategy**:
  1. Split by paragraphs (double newlines)
  2. Split by sentence boundaries (English: `.!?` | Arabic: `؟؛.`)
  3. Fall back to word boundaries for very long units
  4. Create sliding window with overlap

**Usage:**
```python
from chunking import chunk_text

chunks = chunk_text(text, chunk_size=900, overlap=150)
# Returns: ["chunk1", "chunk2", ...]
```

### 3. Embeddings (`embeddings.py`)
- **Model**: `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions)
- **Size**: ~60 MB (lightweight)
- **Performance**: Excellent multilingual semantic understanding
- **Framework**: sentence-transformers

**Usage:**
```python
from embeddings import EmbeddingModel

model = EmbeddingModel()
embeddings = model.encode(["text1", "text2"])
# Returns: numpy array of shape (2, 384)
```

### 4. FAISS Retrieval (`retrieval.py`)
- **Index Type**: IndexFlatL2 (exact L2 distance search)
- **Metric**: L2 distance → Similarity score (1 / (1 + distance))
- **Retrieval**: Top-k similar chunks per query
- **Persistence**: Save/load index and documents to disk

**Usage:**
```python
from retrieval import FAISSRetriever

retriever = FAISSRetriever(dimension=384)
retriever.add_documents(embeddings, documents)
results = retriever.search(query_embedding, k=3)
# Returns: [(document, similarity_score), ...]

# Save and load
retriever.save_index("./index")
retriever = FAISSRetriever.load_index("./index")
```

### 5. Pipeline Orchestrator (`pipeline.py`)
End-to-end RAG pipeline coordinating all components.

**Usage:**
```python
from pipeline import RAGPipeline

# Create pipeline
pipeline = RAGPipeline(chunk_size=900, chunk_overlap=150)

# Process PDFs
chunks_added = pipeline.process_pdfs([Path("doc1.pdf"), Path("doc2.pdf")])

# Retrieve
results = pipeline.retrieve("What are the main requirements?", k=3)
for doc, score in results:
    print(f"Similarity: {score:.4f}")
    print(f"Text: {doc['text'][:200]}...")

# Save index
pipeline.save_index(Path("./indexes"))

# Load later
pipeline = RAGPipeline.load_index(Path("./indexes"))
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# For GPU support, use faiss-gpu instead of faiss-cpu
pip install faiss-gpu
```

## Configuration

### Default Settings
- **Chunk Size**: 900 characters
- **Overlap**: 150 characters
- **Minimum Chunk**: 100 characters
- **Embedding Dimension**: 384 (fixed by model)
- **Retrieval K**: 3 (top-3 results)

### Customize in Pipeline
```python
pipeline = RAGPipeline(
    chunk_size=1024,      # Larger chunks
    chunk_overlap=200,    # More overlap
    embedding_model=custom_model
)
```

## Example: Full Workflow

```python
from pathlib import Path
from pipeline import RAGPipeline

# Setup
project_root = Path(".")
raw_data = project_root / "02_data" / "01_raw"
index_dir = project_root / "03_rag_pipeline" / "indexes"

# Create and populate pipeline
pipeline = RAGPipeline()
for org_folder in raw_data.iterdir():
    if org_folder.is_dir():
        pipeline.process_org_folder(org_folder)

# Save index
pipeline.save_index(index_dir)
print(f"Indexed {pipeline.retriever.index.ntotal} chunks")

# Later: Load and retrieve
pipeline = RAGPipeline.load_index(index_dir)
results = pipeline.retrieve("What are the requirements?", k=5)

for i, (doc, score) in enumerate(results, 1):
    print(f"\n{i}. Score: {score:.4f}")
    print(f"   Document: {doc['document']}")
    print(f"   Page: {doc['page']}")
    print(f"   Text: {doc['text'][:300]}...")
```

## Performance Notes

- **Embedding Generation**: ~100-200 texts/second on CPU (depends on text length)
- **FAISS Indexing**: O(n) for adding documents, O(k*d) for retrieval where d=384
- **Memory**: ~1.5KB per embedding (384 dims × 4 bytes float32)
  - 10,000 chunks ≈ 15MB index + document storage

## Multilingual Support

The pipeline handles:
- **English**: Standard `.!?` sentence endings
- **Arabic**: Arabic punctuation `؟` (question mark), `؛` (semicolon), plus `.`
- **Mixed**: Seamlessly processes code-switched text

Text is normalized to remove diacritics and standardize spacing.

## Saving & Loading

### Saved Structure
```
indexes/
├── faiss.index           # FAISS index binary
├── documents.jsonl       # Document metadata (one per line)
└── config.json          # Pipeline configuration
```

### Load and Continue
```python
from pipeline import RAGPipeline

pipeline = RAGPipeline.load_index(Path("indexes"))

# Continue adding documents
new_chunks = pipeline.process_pdfs([Path("new_doc.pdf")])

# Save updated index
pipeline.save_index(Path("indexes"))
```

## Requirements

| Component | Library | Version |
|-----------|---------|---------|
| PDF Extraction | pymupdf, PyPDF | ≥1.24.0, ≥4.0.0 |
| Embeddings | sentence-transformers | ≥3.0.0 |
| Vector DB | faiss-cpu/gpu | ≥1.8.0 |
| Utilities | numpy, pandas | ≥1.24.0, ≥2.0.0 |

## Troubleshooting

**Issue**: `ImportError: faiss not installed`
- **Solution**: `pip install faiss-cpu` (or `faiss-gpu` for NVIDIA)

**Issue**: `ImportError: sentence-transformers not installed`
- **Solution**: `pip install sentence-transformers`

**Issue**: Slow embedding generation
- **Solution**: Use GPU if available, increase batch_size (default 32)

**Issue**: FAISS index crashes with large datasets
- **Solution**: Consider `IndexIVFFlat` for billions of vectors (requires more memory)

## Future Enhancements

- [ ] Support for other embedding models (OpenAI, Cohere)
- [ ] Hybrid retrieval (BM25 + semantic)
- [ ] Re-ranking with cross-encoders
- [ ] GraphRAG for structured knowledge
- [ ] Batch processing with queue system
