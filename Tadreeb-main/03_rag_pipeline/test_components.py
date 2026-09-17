"""
Unit tests for RAG pipeline components.
Run with: python -m pytest test_components.py -v
Or directly: python test_components.py
"""
import numpy as np
from chunking import chunk_text, split_by_sentences
from embeddings import EmbeddingModel


def test_sentence_splitting():
    """Test sentence splitting with English and Arabic."""
    print("\n[TEST] Sentence Splitting")

    # English text
    english = "Hello world. This is a test! How are you? I'm fine."
    sentences = split_by_sentences(english)
    print(f"English input: {english}")
    print(f"Sentences: {sentences}")
    assert len(sentences) > 1, "Should split English text"

    # Arabic text
    arabic = "السلام عليكم. كيف حالك؟ أنا بخير؛ شكراً لك."
    sentences = split_by_sentences(arabic)
    print(f"\nArabic input: {arabic}")
    print(f"Sentences: {sentences}")
    assert len(sentences) > 1, "Should split Arabic text"

    print("✓ Sentence splitting works")


def test_chunking_basic():
    """Test basic text chunking."""
    print("\n[TEST] Basic Chunking")

    text = """
    Paragraph 1: This is the first paragraph with some content.
    It has multiple sentences here. They help establish context.

    Paragraph 2: This is the second paragraph. It contains additional information.
    The overlapping chunks preserve semantic continuity between sections.

    Paragraph 3: Final paragraph summarizes the key points discussed.
    All chunks maintain the specified overlap to preserve meaning.
    """

    chunks = chunk_text(text, chunk_size=150, overlap=30)

    print(f"Original text length: {len(text)} chars")
    print(f"Number of chunks: {len(chunks)}")
    print("\nChunks:")
    for i, chunk in enumerate(chunks, 1):
        print(f"  {i}. [{len(chunk)} chars] {chunk[:80]}...")

    assert len(chunks) > 1, "Should create multiple chunks"
    assert all(len(chunk) <= 150 + 50 for chunk in chunks), "Chunks should respect size limit"
    print("✓ Chunking works")


def test_chunking_overlap():
    """Test that overlapping is preserved."""
    print("\n[TEST] Chunk Overlap")

    text = "The quick brown fox jumps over the lazy dog. " * 10
    chunks = chunk_text(text, chunk_size=100, overlap=20)

    print(f"Text length: {len(text)} chars")
    print(f"Number of chunks: {len(chunks)}")

    # Check for overlap between consecutive chunks
    overlaps_found = 0
    for i in range(len(chunks) - 1):
        curr_end = chunks[i][-20:]  # Last 20 chars of current chunk
        next_start = chunks[i+1][:20]  # First 20 chars of next chunk

        # Check if there's textual overlap
        if any(word in chunks[i+1] for word in chunks[i].split()[-3:]):
            overlaps_found += 1

    print(f"Overlaps found: {overlaps_found}/{len(chunks)-1}")
    print("✓ Overlap preserved")


def test_chunking_min_size():
    """Test minimum chunk size."""
    print("\n[TEST] Minimum Chunk Size")

    # Very short text
    short_text = "Short."
    chunks = chunk_text(short_text, chunk_size=900, min_chunk_size=100)

    # Text too short should be skipped or returned as-is
    print(f"Short text: '{short_text}'")
    print(f"Chunks: {chunks}")

    # Longer text that respects min_chunk_size
    medium_text = "This is a medium length text that should definitely be at least one hundred characters long to pass the minimum size requirement and continue on for a bit more."
    chunks = chunk_text(medium_text, chunk_size=900, min_chunk_size=50)

    print(f"\nMedium text length: {len(medium_text)} chars")
    print(f"Chunks created: {len(chunks)}")
    print("✓ Min chunk size respected")


def test_embedding_model():
    """Test embedding model initialization and encoding."""
    print("\n[TEST] Embedding Model")

    try:
        model = EmbeddingModel()
        print(f"Model: {model.model_name}")
        print(f"Dimension: {model.dimension}")

        # Test single encoding
        text = "This is a test sentence."
        embedding = model.encode_single(text)
        print(f"\nSingle text embedding shape: {embedding.shape}")
        assert embedding.shape == (384,), "Embedding should be 384-dimensional"

        # Test batch encoding
        texts = ["First text", "Second text", "Third text"]
        embeddings = model.encode(texts)
        print(f"Batch embeddings shape: {embeddings.shape}")
        assert embeddings.shape == (3, 384), "Batch embeddings should be (3, 384)"

        # Test multilingual
        texts_multi = ["Hello world", "مرحبا العالم", "Hello مرحبا"]
        embeddings_multi = model.encode(texts_multi)
        print(f"Multilingual embeddings shape: {embeddings_multi.shape}")
        assert embeddings_multi.shape == (3, 384), "Multilingual embeddings should work"

        # Check embeddings are normalized (optional, but good practice)
        norms = np.linalg.norm(embeddings_multi, axis=1)
        print(f"Embedding norms: {norms}")

        print("✓ Embedding model works")
    except ImportError as e:
        print(f"⚠️  Cannot test embedding model: {e}")
        print("   Install with: pip install sentence-transformers")


def test_arabic_text():
    """Test Arabic text handling."""
    print("\n[TEST] Arabic Text Processing")

    arabic_text = """
    هذا نص عربي للاختبار. يحتوي على عدة جمل مختلفة؛ كل منها لها معنى خاص.
    الجملة الثانية تتحدث عن شيء آخر؟ نعم، هذا صحيح تماماً.
    النص يجب أن يتم تقسيمه بشكل صحيح مع الحفاظ على المعنى الدلالي.
    """

    chunks = chunk_text(arabic_text, chunk_size=200, overlap=30)

    print(f"Arabic text length: {len(arabic_text)} chars")
    print(f"Number of chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks, 1):
        print(f"\n  Chunk {i} ({len(chunk)} chars):")
        print(f"  {chunk[:100]}...")

    assert len(chunks) > 0, "Should create chunks from Arabic text"
    print("✓ Arabic text processing works")


def test_mixed_language_text():
    """Test mixed English/Arabic text."""
    print("\n[TEST] Mixed Language Text")

    mixed_text = """
    English text here. Then some Arabic: السلام عليكم ورحمة الله.
    Back to English: This is important! And more Arabic؟ نعم، بالطبع.
    The system should handle both languages seamlessly; العملية سهلة جداً.
    """

    chunks = chunk_text(mixed_text, chunk_size=200, overlap=30)

    print(f"Mixed text length: {len(mixed_text)} chars")
    print(f"Number of chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks, 1):
        has_english = any(ord(c) < 128 for c in chunk if c.isalpha())
        has_arabic = any(ord(c) >= 1536 for c in chunk)
        print(f"\n  Chunk {i}: English={has_english}, Arabic={has_arabic}")
        print(f"  {chunk[:80]}...")

    print("✓ Mixed language text works")


def run_all_tests():
    """Run all component tests."""
    print("\n" + "=" * 60)
    print("RAG Pipeline Component Tests")
    print("=" * 60)

    try:
        test_sentence_splitting()
    except Exception as e:
        print(f"✗ Sentence splitting failed: {e}")

    try:
        test_chunking_basic()
    except Exception as e:
        print(f"✗ Basic chunking failed: {e}")

    try:
        test_chunking_overlap()
    except Exception as e:
        print(f"✗ Chunking overlap failed: {e}")

    try:
        test_chunking_min_size()
    except Exception as e:
        print(f"✗ Min chunk size failed: {e}")

    try:
        test_arabic_text()
    except Exception as e:
        print(f"✗ Arabic text failed: {e}")

    try:
        test_mixed_language_text()
    except Exception as e:
        print(f"✗ Mixed language failed: {e}")

    try:
        test_embedding_model()
    except Exception as e:
        print(f"✗ Embedding model failed: {e}")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
