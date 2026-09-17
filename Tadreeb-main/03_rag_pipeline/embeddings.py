"""
Embedding generation using sentence-transformers multilingual model.
Model: paraphrase-multilingual-MiniLM-L12-v2 (384 dimensions, ~60MB)
Supports English and Arabic text.
"""
from typing import List, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


class EmbeddingModel:
    """Wrapper for sentence-transformers multilingual model."""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
                 device: Optional[str] = None):
        """
        Initialize embedding model.

        Args:
            model_name: HuggingFace model identifier
            device: Device to use ('cpu', 'cuda', etc). Auto-detected if None.
        """
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

        self.model_name = model_name
        self.model = SentenceTransformer(model_name, device=device)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def encode(self, texts: List[str], batch_size: int = 32,
               show_progress_bar: bool = False) -> np.ndarray:
        """
        Encode texts to embeddings.

        Args:
            texts: List of texts to encode
            batch_size: Batch size for encoding
            show_progress_bar: Show progress bar during encoding

        Returns:
            Numpy array of shape (len(texts), 384)
        """
        return self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True
        )

    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text."""
        return self.encode([text])[0]


def generate_embeddings_batch(texts: List[str], model: Optional[EmbeddingModel] = None,
                             batch_size: int = 32) -> np.ndarray:
    """
    Generate embeddings for a batch of texts.

    Args:
        texts: List of texts to embed
        model: EmbeddingModel instance (creates default if None)
        batch_size: Batch size for processing

    Returns:
        Numpy array of shape (len(texts), 384)
    """
    if model is None:
        model = EmbeddingModel()

    return model.encode(texts, batch_size=batch_size, show_progress_bar=True)


def embed_documents(documents: List[dict], model: Optional[EmbeddingModel] = None,
                   batch_size: int = 32) -> List[dict]:
    """
    Add embeddings to documents.

    Args:
        documents: List of dicts with 'text' field
        model: EmbeddingModel instance (creates default if None)
        batch_size: Batch size for embedding

    Returns:
        List of dicts with added 'embedding' field (numpy array)
    """
    if model is None:
        model = EmbeddingModel()

    texts = [doc.get("text", "") for doc in documents]
    embeddings = generate_embeddings_batch(texts, model=model, batch_size=batch_size)

    result = []
    for doc, embedding in zip(documents, embeddings):
        result.append({
            **doc,
            "embedding": embedding
        })

    return result
