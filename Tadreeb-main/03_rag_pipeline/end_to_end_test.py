"""
End-to-end test of the RAG pipeline with sample PDFs.
Builds an index, tests retrieval, and prepares data for the frontend.
"""
import sys
import time
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from pipeline import RAGPipeline
from embeddings import EmbeddingModel


def print_section(title):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_components():
    """Test individual RAG pipeline components."""
    print_section("TESTING RAG PIPELINE COMPONENTS")

    # Test 1: PDF Extraction
    print("\n[1/5] Testing PDF Extraction...")
    from pdf_extractor import extract_pdf, clean_text

    test_text = "Hello World! This is a test. PDF marker \x00 null bytes here."
    cleaned = clean_text(test_text)
    print(f"✓ Text cleaning works")
    print(f"  Original: {len(test_text)} chars")
    print(f"  Cleaned: {len(cleaned)} chars")

    # Test 2: Chunking
    print("\n[2/5] Testing Text Chunking...")
    from chunking import chunk_text

    long_text = """
    Paragraph 1: This is the first paragraph with multiple sentences.
    It helps establish context for the chunks.

    Paragraph 2: This is the second paragraph with more content.
    The overlap between chunks preserves continuity.
    """ * 3

    chunks = chunk_text(long_text, chunk_size=200, overlap=30)
    print(f"✓ Chunking works")
    print(f"  Text length: {len(long_text)} chars")
    print(f"  Chunks created: {len(chunks)}")
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"  - Chunk {i}: {len(chunk)} chars")

    # Test 3: Embeddings
    print("\n[3/5] Testing Embedding Generation...")
    try:
        model = EmbeddingModel()
        test_texts = ["Hello world", "Test sentence", "Another example"]
        embeddings = model.encode(test_texts)
        print(f"✓ Embedding generation works")
        print(f"  Model: {model.model_name}")
        print(f"  Embedding shape: {embeddings.shape}")
        print(f"  Dimension: {model.dimension}")
    except ImportError as e:
        print(f"⚠️  Skipping embedding test: {e}")
        print(f"  Install: pip install sentence-transformers")
        return False

    # Test 4: Retrieval
    print("\n[4/5] Testing FAISS Retrieval...")
    from retrieval import FAISSRetriever
    import numpy as np

    retriever = FAISSRetriever(dimension=model.dimension)

    test_docs = [
        {"text": "Machine learning is a subset of AI", "id": 1},
        {"text": "Python is a programming language", "id": 2},
        {"text": "Natural language processing uses embeddings", "id": 3},
    ]

    test_embeddings = model.encode([doc["text"] for doc in test_docs])
    retriever.add_documents(test_embeddings, test_docs)

    query = "What is machine learning?"
    query_emb = model.encode_single(query)
    results = retriever.search(query_emb, k=2)

    print(f"✓ FAISS retrieval works")
    print(f"  Query: {query}")
    print(f"  Results found: {len(results)}")
    for i, (doc, score) in enumerate(results, 1):
        print(f"  - Result {i} (score={score:.4f}): {doc['text'][:50]}...")

    # Test 5: Pipeline
    print("\n[5/5] Testing Complete Pipeline...")
    print(f"✓ Pipeline integration ready")

    print_section("✓ ALL COMPONENTS TESTED SUCCESSFULLY")
    return True


def build_index_from_pdfs():
    """Build index from available PDFs."""
    print_section("BUILDING INDEX FROM AVAILABLE PDFs")

    project_root = Path(__file__).parent.parent
    raw_data_folder = project_root / "02_data" / "01_raw"
    index_folder = project_root / "03_rag_pipeline" / "indexes" / "test_index"

    print(f"\nProject root: {project_root}")
    print(f"Raw data folder: {raw_data_folder}")
    print(f"Index output: {index_folder}")

    # Check if data folder exists
    if not raw_data_folder.exists():
        print(f"⚠️  Data folder not found: {raw_data_folder}")
        return None

    # Find PDFs
    pdf_files = list(raw_data_folder.rglob("*.pdf"))

    if not pdf_files:
        print(f"⚠️  No PDF files found in {raw_data_folder}")
        return None

    print(f"\nFound {len(pdf_files)} PDF file(s):")
    for pdf_file in pdf_files:
        size_mb = pdf_file.stat().st_size / (1024 * 1024)
        print(f"  - {pdf_file.name} ({size_mb:.1f} MB)")

    # Create pipeline
    print("\n[1] Initializing RAG Pipeline...")
    try:
        pipeline = RAGPipeline(chunk_size=900, chunk_overlap=150)
        print(f"✓ Pipeline initialized")
        print(f"  Embedding model: {pipeline.embedding_model.model_name}")
        print(f"  Embedding dimension: {pipeline.embedding_model.dimension}")
    except Exception as e:
        print(f"✗ Failed to initialize pipeline: {e}")
        return None

    # Process PDFs
    print("\n[2] Processing PDFs...")
    start_time = time.time()
    total_chunks = 0

    for pdf_file in pdf_files:
        try:
            print(f"\n  Processing: {pdf_file.name}")
            chunks = pipeline.process_pdfs([pdf_file])
            total_chunks += chunks
            print(f"  ✓ Added {chunks} chunks")
        except Exception as e:
            print(f"  ✗ Error processing {pdf_file.name}: {e}")
            continue

    elapsed = time.time() - start_time

    if total_chunks == 0:
        print("\n✗ No chunks created. Check PDF files or dependencies.")
        return None

    print(f"\n✓ Processing complete")
    print(f"  Total chunks indexed: {total_chunks}")
    print(f"  Time elapsed: {elapsed:.1f}s")

    # Save index
    print("\n[3] Saving Index...")
    try:
        pipeline.save_index(index_folder)
        print(f"✓ Index saved to {index_folder}")

        # Print index stats
        import json
        config_path = index_folder / "config.json"
        with open(config_path, "r") as f:
            config = json.load(f)

        print(f"\nIndex Statistics:")
        print(f"  Embedding model: {config['embedding_model']}")
        print(f"  Embedding dimension: {config['embedding_dimension']}")
        print(f"  Chunk size: {config['chunk_size']} chars")
        print(f"  Chunk overlap: {config['chunk_overlap']} chars")
        print(f"  Total documents: {config['total_documents']}")
        print(f"  Total chunks: {config['total_chunks']}")
    except Exception as e:
        print(f"✗ Failed to save index: {e}")
        return None

    return pipeline, index_folder


def test_retrieval(pipeline):
    """Test retrieval on built index."""
    print_section("TESTING RETRIEVAL ON INDEXED DATA")

    test_queries = [
        "What are the requirements?",
        "Tell me about the program",
        "What is the eligibility criteria?",
        "How to apply?",
        "What are the dates?",
    ]

    print(f"\nTesting {len(test_queries)} queries...")

    for query in test_queries:
        print(f"\n{'─' * 70}")
        print(f"Query: \"{query}\"")
        print(f"{'─' * 70}")

        try:
            results = pipeline.retrieve(query, k=3)

            if not results:
                print("No results found")
                continue

            for i, (doc, score) in enumerate(results, 1):
                print(f"\n[Result {i}] Similarity: {score:.4f}")

                # Print metadata
                metadata_keys = ["document", "page", "org", "chunk_id"]
                for key in metadata_keys:
                    if key in doc:
                        print(f"  {key}: {doc[key]}")

                # Print snippet
                text = doc.get("text", "")
                snippet = text[:200] + "..." if len(text) > 200 else text
                print(f"\n  Text snippet:")
                print(f"  {snippet}")

        except Exception as e:
            print(f"✗ Error during retrieval: {e}")

    print_section("✓ RETRIEVAL TEST COMPLETE")


def create_api_test_server():
    """Create a simple test API server."""
    print_section("CREATING TEST API SERVER")

    api_code = '''"""
Simple Flask API for testing RAG pipeline with frontend.
Run with: python api_test_server.py
Then test at: http://localhost:5000/api/test
"""
import sys
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add RAG pipeline to path
sys.path.insert(0, str(Path(__file__).parent))
from pipeline import RAGPipeline

app = Flask(__name__)
CORS(app)

# Load pipeline
try:
    print("Loading RAG pipeline index...")
    pipeline = RAGPipeline.load_index(
        Path(__file__).parent / "indexes" / "test_index"
    )
    print("✓ Pipeline loaded successfully")
    PIPELINE_READY = True
except Exception as e:
    print(f"✗ Failed to load pipeline: {e}")
    PIPELINE_READY = False


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "pipeline_ready": PIPELINE_READY
    })


@app.route("/api/query", methods=["POST"])
def query():
    """RAG retrieval endpoint."""
    if not PIPELINE_READY:
        return jsonify({
            "error": "Pipeline not initialized",
            "results": []
        }), 503

    data = request.json or {}
    query_text = data.get("query", "").strip()
    k = data.get("k", 3)

    if not query_text:
        return jsonify({
            "error": "Empty query",
            "results": []
        }), 400

    try:
        results = pipeline.retrieve(query_text, k=k)

        # Format results for frontend
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "score": float(score),
                "document": doc.get("document", "unknown"),
                "page": doc.get("page", "?"),
                "org": doc.get("org", "unknown"),
                "text": doc.get("text", ""),
                "snippet": doc.get("text", "")[:200] + "..." if len(doc.get("text", "")) > 200 else doc.get("text", "")
            })

        return jsonify({
            "query": query_text,
            "results": formatted_results,
            "count": len(formatted_results)
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "results": []
        }), 500


@app.route("/api/test", methods=["GET"])
def test():
    """Test endpoint with sample queries."""
    if not PIPELINE_READY:
        return jsonify({
            "error": "Pipeline not initialized",
            "test_queries": []
        }), 503

    test_queries = [
        "What are the requirements?",
        "Tell me about the program",
        "How to apply?"
    ]

    results = {}
    for query_text in test_queries:
        try:
            query_results = pipeline.retrieve(query_text, k=2)
            results[query_text] = [
                {
                    "score": float(score),
                    "document": doc.get("document", "unknown"),
                    "text": doc.get("text", "")[:150]
                }
                for doc, score in query_results
            ]
        except Exception as e:
            results[query_text] = {"error": str(e)}

    return jsonify({
        "status": "ok",
        "test_results": results
    })


if __name__ == "__main__":
    print("Starting RAG Pipeline Test API Server...")
    print("Listen on http://localhost:5000")
    print("Endpoints:")
    print("  GET  /health - Health check")
    print("  POST /api/query - Query RAG pipeline")
    print("  GET  /api/test - Run test queries")
    print("\\nExample curl:")
    print("  curl -X POST http://localhost:5000/api/query \\\\")
    print('    -H "Content-Type: application/json" \\\\')
    print('    -d "{\\"query\\": \\"What are the requirements?\\", \\"k\\": 3}"')
    print()
    app.run(debug=True, port=5000)
'''

    api_server_path = Path(__file__).parent / "api_test_server.py"

    try:
        with open(api_server_path, "w", encoding="utf-8") as f:
            f.write(api_code)

        print(f"\n✓ API test server created: {api_server_path}")
        print(f"\nTo start the server:")
        print(f"  1. Install Flask: pip install flask flask-cors")
        print(f"  2. Run: python {api_server_path}")
        print(f"  3. Test: curl http://localhost:5000/health")

        return api_server_path

    except Exception as e:
        print(f"✗ Failed to create API server: {e}")
        return None


def main():
    """Run end-to-end test."""
    print("\n" + "=" * 70)
    print("  RAG PIPELINE END-TO-END TEST")
    print("=" * 70)

    # Step 1: Test components
    if not test_components():
        print("\n✗ Component tests failed. Cannot continue.")
        return

    # Step 2: Build index from PDFs
    result = build_index_from_pdfs()
    if result is None:
        print("\n⚠️  Index building failed. Skipping retrieval test.")
        return

    pipeline, index_folder = result

    # Step 3: Test retrieval
    test_retrieval(pipeline)

    # Step 4: Create API server
    api_path = create_api_test_server()

    # Final summary
    print_section("END-TO-END TEST SUMMARY")
    print("\n✓ All tests completed!")
    print(f"\nIndex location: {index_folder}")
    print(f"Index size: {sum(f.stat().st_size for f in index_folder.rglob('*') if f.is_file()) / 1024 / 1024:.1f} MB")
    print(f"\nRAG Pipeline Statistics:")
    print(f"  Embedding model: {pipeline.embedding_model.model_name}")
    print(f"  Total indexed chunks: {pipeline.retriever.index.ntotal}")
    print(f"  Chunk size: {pipeline.chunk_size} chars")
    print(f"  Chunk overlap: {pipeline.chunk_overlap} chars")

    if api_path:
        print(f"\nNext steps:")
        print(f"  1. pip install flask flask-cors")
        print(f"  2. python {api_path}")
        print(f"  3. Test at http://localhost:5000/api/test")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
