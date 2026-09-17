"""
Complete RAG pipeline orchestration.
Flow: PDF → Extract Text → Clean → Chunk → Embed → Index → Retrieve
"""
import json
from pathlib import Path
from typing import List, Optional, Tuple
import hashlib

from pdf_extractor import extract_pdf, extract_org_pdfs, clean_text
from chunking import chunk_documents
from embeddings import EmbeddingModel, embed_documents
from retrieval import FAISSRetriever, RetrieverPipeline


class RAGPipeline:
    """End-to-end RAG pipeline."""

    def __init__(self, embedding_model: Optional[EmbeddingModel] = None,
                 chunk_size: int = 900, chunk_overlap: int = 150):
        """
        Initialize RAG pipeline.

        Args:
            embedding_model: EmbeddingModel instance (creates default if None)
            chunk_size: Character size for chunks
            chunk_overlap: Character overlap between chunks
        """
        self.embedding_model = embedding_model or EmbeddingModel()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.retriever = FAISSRetriever(dimension=self.embedding_model.dimension)
        self.retriever_pipeline = RetrieverPipeline(
            self.retriever,
            embedding_model=self.embedding_model
        )

        self.indexed_documents = []

    def process_pdfs(self, pdf_paths: List[Path]) -> int:
        """
        Process PDFs and add to index.

        Args:
            pdf_paths: List of PDF file paths

        Returns:
            Number of chunks indexed
        """
        all_documents = []

        for pdf_path in pdf_paths:
            print(f"Processing {pdf_path.name}...")
            pages = extract_pdf(pdf_path)

            # Add document metadata
            document_id = hashlib.sha256(Path(pdf_path).read_bytes()).hexdigest()[:16]
            for page in pages:
                page.update({
                    "source": str(pdf_path),
                    "document_id": document_id,
                    "source_type": "pdf"
                })
                all_documents.append(page)

        # Chunk documents
        print(f"Chunking {len(all_documents)} pages...")
        chunked_docs = chunk_documents(
            all_documents,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        print(f"Created {len(chunked_docs)} chunks")

        # Embed and index
        print("Generating embeddings...")
        embedded_docs = embed_documents(
            chunked_docs,
            model=self.embedding_model,
            batch_size=32
        )

        # Extract embeddings for FAISS
        import numpy as np
        embeddings = np.array([doc["embedding"] for doc in embedded_docs])

        # Remove embeddings from documents before storing (to save memory)
        docs_for_index = [
            {k: v for k, v in doc.items() if k != "embedding"}
            for doc in embedded_docs
        ]

        # Add to index
        print("Indexing with FAISS...")
        self.retriever.add_documents(embeddings, docs_for_index)
        self.indexed_documents.extend(docs_for_index)

        return len(chunked_docs)

    def process_org_folder(self, org_folder: Path) -> int:
        """
        Process all PDFs in <org>/official/ directory.

        Args:
            org_folder: Path to organization folder

        Returns:
            Number of chunks indexed
        """
        org = org_folder.name
        print(f"\nProcessing organization: {org}")

        pages = extract_org_pdfs(org_folder)
        if not pages:
            print(f"No PDFs found in {org_folder / 'official'}")
            return 0

        print(f"Extracted {len(pages)} pages from {org}")

        # Chunk documents
        print("Chunking...")
        chunked_docs = chunk_documents(
            pages,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        print(f"Created {len(chunked_docs)} chunks")

        # Embed and index
        print("Generating embeddings...")
        embedded_docs = embed_documents(
            chunked_docs,
            model=self.embedding_model,
            batch_size=32
        )

        # Extract embeddings for FAISS
        import numpy as np
        embeddings = np.array([doc["embedding"] for doc in embedded_docs])

        # Remove embeddings from documents before storing
        docs_for_index = [
            {k: v for k, v in doc.items() if k != "embedding"}
            for doc in embedded_docs
        ]

        # Add to index
        print("Indexing with FAISS...")
        self.retriever.add_documents(embeddings, docs_for_index)
        self.indexed_documents.extend(docs_for_index)

        return len(chunked_docs)

    def retrieve(self, query: str, k: int = 3) -> List[Tuple[dict, float]]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Query text
            k: Number of results

        Returns:
            List of (document, similarity_score) tuples
        """
        return self.retriever_pipeline.retrieve(query, k=k)

    def retrieve_batch(self, queries: List[str], k: int = 3):
        """Retrieve results for multiple queries."""
        return self.retriever_pipeline.retrieve_batch(queries, k=k)

    def save_index(self, save_path: Path):
        """Save indexed data to disk."""
        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)

        print(f"Saving index to {save_path}...")
        self.retriever.save_index(save_path)

        # Save pipeline config
        config = {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "embedding_model": self.embedding_model.model_name,
            "embedding_dimension": self.embedding_model.dimension,
            "total_documents": len(self.indexed_documents),
            "total_chunks": self.retriever.index.ntotal
        }

        config_path = save_path / "config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(self.indexed_documents)} documents, {self.retriever.index.ntotal} chunks")

    @classmethod
    def load_index(cls, index_path: Path) -> "RAGPipeline":
        """Load pipeline from saved index."""
        index_path = Path(index_path)

        # Load config
        config_path = index_path / "config.json"
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Create pipeline
        embedding_model = EmbeddingModel(config["embedding_model"])
        pipeline = cls(
            embedding_model=embedding_model,
            chunk_size=config["chunk_size"],
            chunk_overlap=config["chunk_overlap"]
        )

        # Load retriever
        print("Loading FAISS index...")
        pipeline.retriever = FAISSRetriever.load_index(index_path, embeddings=None)
        pipeline.retriever_pipeline = RetrieverPipeline(
            pipeline.retriever,
            embedding_model=embedding_model
        )
        pipeline.indexed_documents = pipeline.retriever.documents

        print(f"Loaded {len(pipeline.indexed_documents)} documents from {index_path}")

        return pipeline


def create_pipeline_from_org(org_folder: Path,
                            save_path: Optional[Path] = None) -> RAGPipeline:
    """
    Create and populate RAG pipeline from organization folder.

    Args:
        org_folder: Path to organization folder with PDFs
        save_path: Optional path to save the index

    Returns:
        RAGPipeline instance
    """
    pipeline = RAGPipeline()
    chunks_added = pipeline.process_org_folder(org_folder)

    if chunks_added > 0 and save_path:
        pipeline.save_index(save_path)

    return pipeline


if __name__ == "__main__":
    # Example usage
    from pathlib import Path

    # Set paths
    project_root = Path(__file__).parent.parent
    raw_data_folder = project_root / "02_data" / "01_raw"
    index_folder = project_root / "03_rag_pipeline" / "indexes"

    # Create pipeline
    pipeline = RAGPipeline()

    # Process all organizations
    total_chunks = 0
    if raw_data_folder.exists():
        for org_folder in sorted(raw_data_folder.iterdir()):
            if org_folder.is_dir():
                chunks = pipeline.process_org_folder(org_folder)
                total_chunks += chunks

    # Save index
    if total_chunks > 0:
        pipeline.save_index(index_folder)
        print(f"\nTotal chunks indexed: {total_chunks}")

        # Test retrieval
        print("\n--- Testing retrieval ---")
        test_query = "What are the main requirements?"
        results = pipeline.retrieve(test_query, k=3)

        print(f"\nQuery: {test_query}")
        for i, (doc, score) in enumerate(results, 1):
            print(f"\n{i}. Similarity: {score:.4f}")
            print(f"   Source: {doc.get('document', 'unknown')}")
            print(f"   Org: {doc.get('org', 'unknown')}")
            print(f"   Text: {doc.get('text', '')[:200]}...")
