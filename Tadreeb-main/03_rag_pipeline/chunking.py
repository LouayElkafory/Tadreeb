"""
Overlapping + sentence-aware chunking for English and Arabic text.
Chunk size: 900 chars, Overlap: 150 chars, Min chunk: 100 chars.
"""
import re
from typing import List


# Regex patterns for sentence boundaries (English and Arabic)
SENTENCE_ENDINGS = re.compile(r'[.!?؟؛]+')
# Arabic punctuation: ؟ (question mark), ؛ (semicolon), . (period)


def split_by_sentences(text: str) -> List[str]:
    """Split text into sentences respecting both English and Arabic punctuation."""
    if not text:
        return []

    # Split on sentence endings: .!? and Arabic ؟؛
    pattern = r'(?<=[.!?؟؛])\s+'
    sentences = re.split(pattern, text.strip())

    # Process sentences and handle very long ones
    result = []
    for sentence in sentences:
        if not sentence.strip():
            continue

        # For very long sentences, split on Arabic commas (،)
        if len(sentence) > 200 and '،' in sentence:
            subsents = sentence.split('،')
            for subsent in subsents:
                if subsent.strip() and len(subsent.strip()) > 3:
                    result.append(subsent.strip())
        else:
            if len(sentence.strip()) > 3:
                result.append(sentence.strip())

    return result


def split_by_words(text: str) -> List[str]:
    """Fallback: split by word boundaries."""
    return text.split()


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150,
               min_chunk_size: int = 100) -> List[str]:
    """
    Create overlapping chunks with sentence awareness.

    Strategy:
    1. Split by paragraphs
    2. Split by sentence boundaries (handles English .!? and Arabic ؟؛)
    3. Fall back to word boundaries for very long units
    4. Create sliding window with overlap

    Args:
        text: Input text to chunk
        chunk_size: Target chunk size in characters (default 900)
        overlap: Overlap size in characters (default 150)
        min_chunk_size: Minimum chunk size (default 100)

    Returns:
        List of text chunks with overlap
    """
    if not text or len(text.strip()) < min_chunk_size:
        return [text.strip()] if text.strip() else []

    # Step 1: Split by paragraphs (double newline)
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    # Step 2: Process each paragraph into sentences
    all_sentences = []
    for paragraph in paragraphs:
        sentences = split_by_sentences(paragraph)
        if not sentences:
            # Fallback: treat paragraph as single unit
            sentences = [paragraph]
        all_sentences.extend(sentences)

    # Step 3: Build chunks by combining sentences
    chunks = []
    current_chunk = ""

    for sentence in all_sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Check if adding this sentence exceeds chunk_size
        test_chunk = current_chunk + " " + sentence if current_chunk else sentence

        if len(test_chunk) <= chunk_size:
            current_chunk = test_chunk
        else:
            # Sentence doesn't fit, save current chunk if it's large enough
            if len(current_chunk) >= min_chunk_size:
                chunks.append(current_chunk)

            # If single sentence is too long, split it by words
            if len(sentence) > chunk_size:
                words = split_by_words(sentence)
                word_chunk = ""
                for word in words:
                    test_word_chunk = word_chunk + " " + word if word_chunk else word
                    if len(test_word_chunk) <= chunk_size:
                        word_chunk = test_word_chunk
                    else:
                        if len(word_chunk) >= min_chunk_size:
                            chunks.append(word_chunk)
                        word_chunk = word
                if len(word_chunk) >= min_chunk_size:
                    chunks.append(word_chunk)
                current_chunk = ""
            else:
                # Start new chunk with this sentence
                current_chunk = sentence

    # Don't forget the last chunk
    if len(current_chunk) >= min_chunk_size:
        chunks.append(current_chunk)

    # Step 4: Apply overlap sliding window
    if not chunks:
        return []

    overlapped_chunks = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            overlapped_chunks.append(chunk)
        else:
            # Get the overlap from the end of previous chunk
            prev_chunk = overlapped_chunks[-1]
            if len(prev_chunk) > overlap:
                overlap_text = prev_chunk[-overlap:]
                new_chunk = overlap_text + " " + chunk
            else:
                new_chunk = prev_chunk + " " + chunk
            overlapped_chunks.append(new_chunk)

    return overlapped_chunks


def chunk_documents(documents: List[dict], chunk_size: int = 900,
                   overlap: int = 150) -> List[dict]:
    """
    Chunk a list of documents (with text field) and preserve metadata.

    Args:
        documents: List of dicts with at least 'text' and 'page' fields
        chunk_size: Target chunk size in characters
        overlap: Overlap size in characters

    Returns:
        List of dicts with chunks and original metadata
    """
    chunked_docs = []

    for doc in documents:
        text = doc.get("text", "")
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

        for chunk_idx, chunk in enumerate(chunks):
            chunked_doc = {
                **doc,
                "text": chunk,
                "chunk_id": chunk_idx,
                "total_chunks": len(chunks),
            }
            chunked_docs.append(chunked_doc)

    return chunked_docs
