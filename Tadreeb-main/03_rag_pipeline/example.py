"""
Quick-start example: Build and query a RAG pipeline.
"""
from pathlib import Path
from pipeline import RAGPipeline


def main():
    # Setup paths
    project_root = Path(__file__).parent.parent
    raw_data_folder = project_root / "02_data" / "01_raw"
    index_folder = project_root / "03_rag_pipeline" / "indexes"

    print("=" * 60)
    print("RAG Pipeline Example: Build Index and Retrieve")
    print("=" * 60)

    # Step 1: Create pipeline
    print("\n[1] Creating RAG pipeline...")
    pipeline = RAGPipeline(
        chunk_size=900,
        chunk_overlap=150
    )

    # Step 2: Process PDFs
    print("\n[2] Processing PDFs from organizations...")
    total_chunks = 0

    if not raw_data_folder.exists():
        print(f"   ⚠️  Data folder not found: {raw_data_folder}")
        print("   Create sample data or update the path.")
        return

    for org_folder in sorted(raw_data_folder.iterdir()):
        if org_folder.is_dir():
            chunks = pipeline.process_org_folder(org_folder)
            total_chunks += chunks

    if total_chunks == 0:
        print("   ⚠️  No PDFs found. Add PDFs to 02_data/01_raw/<org>/official/")
        return

    print(f"\n   ✓ Total chunks created: {total_chunks}")

    # Step 3: Save index
    print(f"\n[3] Saving index to {index_folder}...")
    pipeline.save_index(index_folder)
    print("   ✓ Index saved")

    # Step 4: Test retrieval
    print("\n[4] Testing retrieval...")
    test_queries = [
        "What are the main requirements?",
        "Tell me about the process",
        "What are the key features?",
    ]

    for query in test_queries:
        print(f"\n   Query: \"{query}\"")
        results = pipeline.retrieve(query, k=3)

        if not results:
            print("   ⚠️  No results found")
            continue

        for i, (doc, score) in enumerate(results, 1):
            print(f"\n   {i}. Relevance: {score:.4f}")

            # Print metadata
            if "document" in doc:
                print(f"      Document: {doc['document']}")
            if "page" in doc:
                print(f"      Page: {doc['page']}")
            if "org" in doc:
                print(f"      Organization: {doc['org']}")
            if "chunk_id" in doc:
                print(f"      Chunk: {doc['chunk_id']}")

            # Print snippet (first 200 chars)
            text = doc.get("text", "")
            snippet = text[:200] + "..." if len(text) > 200 else text
            print(f"      Text: {snippet}")

    # Step 5: Show stats
    print("\n[5] Pipeline Statistics")
    print(f"   Embedding Model: {pipeline.embedding_model.model_name}")
    print(f"   Embedding Dimension: {pipeline.embedding_model.dimension}")
    print(f"   Total Indexed Chunks: {pipeline.retriever.index.ntotal}")
    print(f"   Total Documents: {len(pipeline.indexed_documents)}")
    print(f"   Chunk Size: {pipeline.chunk_size} chars")
    print(f"   Chunk Overlap: {pipeline.chunk_overlap} chars")

    # Step 6: Show how to load later
    print("\n[6] To load the index later:")
    print("   ```python")
    print("   from pipeline import RAGPipeline")
    print(f"   pipeline = RAGPipeline.load_index(Path('{index_folder}'))")
    print("   results = pipeline.retrieve('your query', k=3)")
    print("   ```")

    print("\n" + "=" * 60)
    print("✓ Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
