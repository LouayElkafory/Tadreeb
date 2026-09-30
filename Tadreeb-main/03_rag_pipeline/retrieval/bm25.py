"""
A small in-memory BM25 index over the chunk corpus.

Dense embeddings alone were missing a lot of these questions: the corpus is
mostly English PDF text, the questions are Egyptian Arabic, and a multilingual
MiniLM only loosely aligns the two. But the terms that actually identify an
answer - "DevOps", "DEPI", "Fortinet", "164", "ITI" - are written identically in
both languages, and exact term matching finds them reliably where the embedding
does not. BM25 covers that half; the dense search covers paraphrase.

The corpus is a few hundred chunks, so a plain Python index is more than fast
enough and avoids another dependency.
"""
import math
from collections import Counter

K1 = 1.5
B = 0.75


class BM25:
    def __init__(self, documents: list[list[str]]):
        self.documents = documents
        self.doc_count = len(documents)
        self.doc_lengths = [len(d) for d in documents]
        self.avg_length = (sum(self.doc_lengths) / self.doc_count) if self.doc_count else 0.0
        self.term_frequencies = [Counter(d) for d in documents]

        document_frequency = Counter()
        for doc in documents:
            document_frequency.update(set(doc))
        # Standard BM25+ style idf floor, so a term present in most documents
        # contributes ~0 instead of going negative and penalising a good match.
        self.idf = {
            term: max(
                math.log((self.doc_count - freq + 0.5) / (freq + 0.5) + 1.0),
                0.0,
            )
            for term, freq in document_frequency.items()
        }

    def scores(self, query_terms: list[str]) -> list[float]:
        """BM25 score of every document against the query."""
        results = [0.0] * self.doc_count
        if not self.doc_count or not self.avg_length:
            return results
        for term in query_terms:
            idf = self.idf.get(term)
            if not idf:
                continue
            for index, frequencies in enumerate(self.term_frequencies):
                freq = frequencies.get(term)
                if not freq:
                    continue
                norm = 1 - B + B * (self.doc_lengths[index] / self.avg_length)
                results[index] += idf * (freq * (K1 + 1)) / (freq + K1 * norm)
        return results
