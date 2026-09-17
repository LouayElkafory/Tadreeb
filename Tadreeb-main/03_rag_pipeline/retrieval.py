"""
FAISS-based vector database indexing and retrieval.
Index type: IndexFlatL2 (exact search using L2 distance)
Retrieval metric: L2 distance converted to similarity score
"""
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
import json

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False


class FAISSRetriever:
    """FAISS-based vector database for retrieval."""

    def __init__(self, dimension: int = 384, index_type: str = "flat"):
        """
        Initialize FAISS retriever.

        Args:
            dimension: Embedding dimension (384 for paraphrase-multilingual-MiniLM-L12-v2)
            index_type: Type of index ('flat' for exact L2 search)
        """
        if not HAS_FAISS:
            raise ImportError(
                "faiss not installed. "
                "Install with: pip install faiss-cpu (or faiss-gpu)"
            )

        self.dimension = dimension
        self.index_type = index_type

        if index_type == "flat":
            self.index = faiss.IndexFlatL2(dimension)
        else:
            raise ValueError(f"Unsupported index type: {index_type}")

        self.documents = []  # Store original documents for retrieval

    def add_documents(self, embeddings: np.ndarray, documents: List[dict]):
        """
        Add documents and their embeddings to the index.

        Args:
            embeddings: Numpy array of shape (n_docs, dimension)
            documents: List of document dicts with metadata
        """
        if embeddings.shape[0] != len(documents):
            raise ValueError("Number of embeddings must match number of documents")

        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch: got {embeddings.shape[1]}, "
                f"expected {self.dimension}"
            )

        # Ensure embeddings are float32 (required by FAISS)
        embeddings = embeddings.astype(np.float32)

        # Add to FAISS index
        self.index.add(embeddings)

        # Store original documents
        self.documents.extend(documents)

    def search(self, query_embedding: np.ndarray, k: int = 3) -> List[Tuple[dict, float]]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query embedding (shape: (dimension,) or (1, dimension))
            k: Number of results to return

        Returns:
            List of (document, similarity_score) tuples, sorted by similarity desc.
            Similarity score: 1 / (1 + l2_distance)
        """
        if isinstance(query_embedding, np.ndarray) and query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        query_embedding = query_embedding.astype(np.float32)

        if self.index.ntotal == 0:
            return []

        # Search (returns distances and indices)
        distances, indices = self.index.search(query_embedding, min(k, self.index.ntotal))

        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1:  # Invalid result
                continue

            # Convert L2 distance to similarity score
            similarity = 1.0 / (1.0 + float(distance))

            doc = self.documents[idx]
            results.append((doc, similarity))

        return sorted(results, key=lambda x: x[1], reverse=True)

    def save_index(self, index_path: Path):
        """Save FAISS index and documents to disk."""
        index_path = Path(index_path)
        index_path.parent.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.index, str(index_path / "faiss.index"))

        # Save documents as JSONL
        docs_path = index_path / "documents.jsonl"
        with open(docs_path, "w", encoding="utf-8") as f:
            for doc in self.documents:
                # Remove embeddings from saved documents (too large, can be regenerated)
                doc_without_embedding = {k: v for k, v in doc.items() if k != "embedding"}
                f.write(json.dumps(doc_without_embedding, ensure_ascii=False) + "\n")

    @classmethod
    def load_index(cls, index_path: Path, embeddings=None) -> "FAISSRetriever":
        """
        Load FAISS index and documents from disk.

        Args:
            index_path: Path to directory containing faiss.index and documents.jsonl
            embeddings: Optional EmbeddingModel to regenerate embeddings from text

        Returns:
            FAISSRetriever instance
        """
        index_path = Path(index_path)

        # Load FAISS index
        index = faiss.read_index(str(index_path / "faiss.index"))
        dimension = index.d

        # Create retriever
        retriever = cls(dimension=dimension)
        retriever.index = index

        # Load documents
        docs_path = index_path / "documents.jsonl"
        documents = []
        with open(docs_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    doc = json.loads(line)
                    documents.append(doc)

        retriever.documents = documents

        # Regenerate embeddings if provided
        if embeddings is not None:
            texts = [doc.get("text", "") for doc in documents]
            embeddings_array = embeddings.encode(texts, show_progress_bar=True)

            # Recreate index with embeddings
            retriever.index = faiss.IndexFlatL2(dimension)
            retriever.index.add(embeddings_array.astype(np.float32))

        return retriever


class RetrieverPipeline:
    """Complete retrieval pipeline: embedding → search."""

    def __init__(self, retriever: FAISSRetriever,
                 embedding_model=None):
        """
        Initialize retrieval pipeline.

        Args:
            retriever: FAISSRetriever instance
            embedding_model: EmbeddingModel for encoding queries
        """
        self.retriever = retriever
        self.embedding_model = embedding_model

    def retrieve(self, query: str, k: int = 3) -> List[Tuple[dict, float]]:
        """
        Retrieve documents for a query.

        Args:
            query: Query text
            k: Number of results

        Returns:
            List of (document, similarity_score) tuples
        """
        if self.embedding_model is None:
            raise ValueError("Embedding model not initialized")

        # Encode query
        query_embedding = self.embedding_model.encode_single(query)

        # Search
        return self.retriever.search(query_embedding, k=k)

    def retrieve_batch(self, queries: List[str], k: int = 3) -> List[List[Tuple[dict, float]]]:
        """
        Retrieve documents for multiple queries.

        Args:
            queries: List of query texts
            k: Number of results per query

        Returns:
            List of lists of (document, similarity_score) tuples
        """
        if self.embedding_model is None:
            raise ValueError("Embedding model not initialized")

        # Encode queries
        query_embeddings = self.embedding_model.encode(queries)

        # Search each query
        results = []
        for query_embedding in query_embeddings:
            result = self.retriever.search(query_embedding, k=k)
            results.append(result)

        return results
