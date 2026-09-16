"""
retriever.py
البحث: similarity search + فلترة metadata (program_name, info_type)

بيتصل بـ ChromaDB المحلية (اللي اتبنت في embed_and_store.py) وبيستخدم
نموذج الـembedding المحلي عن طريق Ollama (نفس الموديل اللي اتستخدم وقت
التخزين - افتراضيًا nomic-embed-text) عشان يحول سؤال المستخدم لمتجه،
وبعدين يجيب أقرب الـchunks من نفس النوع (program_name / info_type لو
اتحددوا) من المستندات الرسمية.

الاستخدام الأساسي:

    from retriever import Retriever

    retriever = Retriever()
    results = retriever.retrieve(
        query="ايه شروط التقديم في رواد مصر الرقمية؟",
        program_name="depi",   # اختياري: iti / nti / depi
        info_type=None,        # اختياري: eligibility / deadline / contact ...
        top_k=5,
    )
    for r in results:
        print(r["score"], r["metadata"], r["text"][:80])
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import chromadb
import ollama

# vector_db_config.py (03_rag_pipeline/embeddings/) is the single source of
# truth for the DB path / collection / embedding model, so storage
# (embed_and_store.py) and retrieval (here) can never drift apart.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "embeddings"))
from vector_db_config import (  # noqa: E402
    COLLECTION_NAME as DEFAULT_COLLECTION_NAME,
    VECTOR_DB_PATH as DEFAULT_PERSIST_DIR,
    EMBEDDING_MODEL as DEFAULT_EMBEDDING_MODEL,
)

logger = logging.getLogger(__name__)

# القيم المسموحة للفلترة - لازم تفضل متسقة مع قيم "org" الفعلية في الـmetadata
VALID_PROGRAM_NAMES = {"iti", "nti", "depi", "itida"}


@dataclass
class RetrievedChunk:
    """نتيجة استرجاع واحدة، بشكل موحّد وسهل الاستخدام في باقي الـpipeline."""

    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"text": self.text, "score": self.score, "metadata": self.metadata}


class RetrieverError(RuntimeError):
    """خطأ عام في مرحلة الاسترجاع (اتصال بالـDB أو بالـembedding model)."""


class Retriever:
    def __init__(
        self,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        persist_directory: str = DEFAULT_PERSIST_DIR,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        ollama_client: Optional["ollama.Client"] = None,
    ) -> None:
        self.embedding_model = embedding_model
        self.ollama_client = ollama_client or ollama.Client()

        try:
            self._chroma_client = chromadb.PersistentClient(path=persist_directory)
            self._collection = self._chroma_client.get_collection(collection_name)
        except Exception as exc:  # noqa: BLE001 - عايزين رسالة واضحة للمستخدم
            raise RetrieverError(
                f"مش قادر أفتح الـcollection '{collection_name}' من '{persist_directory}'. "
                "اتأكد إن embed_and_store.py اتشغل قبل كده وعمل تخزين للـchunks. "
                f"تفاصيل الخطأ: {exc}"
            ) from exc

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def retrieve(
        self,
        query: str,
        program_name: Optional[str] = None,
        info_type: Optional[str] = None,
        top_k: int = 5,
        min_score: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """
        يرجع أقرب top_k نتائج للسؤال، مع فلترة اختيارية بالـmetadata.

        program_name: "iti" | "nti" | "depi" (أو None لكل البرامج)
        info_type: زي "eligibility" / "deadline" / "contact" ... (حسب الـschema)
        min_score: لو محدد، بيشيل أي نتيجة أضعف من العتبة دي (0..1، الأعلى أفضل)
        """
        if not query or not query.strip():
            raise ValueError("السؤال (query) لازم ميبقاش فاضي")

        if program_name is not None and program_name not in VALID_PROGRAM_NAMES:
            logger.warning(
                "program_name '%s' مش من القيم المعروفة %s - هيتبعت زي ما هو للفلتر",
                program_name,
                VALID_PROGRAM_NAMES,
            )

        query_embedding = self._embed(query)
        where_filter = self._build_where_filter(program_name, info_type)

        raw = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter if where_filter else None,
        )

        results = self._parse_results(raw)

        if min_score is not None:
            results = [r for r in results if r.score >= min_score]

        return [r.as_dict() for r in results]

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _embed(self, text: str) -> list[float]:
        try:
            response = self.ollama_client.embeddings(model=self.embedding_model, prompt=text)
        except Exception as exc:  # noqa: BLE001
            raise RetrieverError(
                f"فشل الاتصال بـ Ollama لعمل embedding (موديل: {self.embedding_model}). "
                "اتأكد إن 'ollama serve' شغالة والموديل متحمّل (ollama pull "
                f"{self.embedding_model}). تفاصيل: {exc}"
            ) from exc
        return response["embedding"]

    @staticmethod
    def _build_where_filter(
        program_name: Optional[str], info_type: Optional[str]
    ) -> dict[str, Any]:
        """
        بيبني فلتر Chroma على الـmetadata اللي فعلاً موجودة في الـchunks
        (org / document / page - شوف chunker.py و embed_and_store.py).
        program_name بيتفلتر على مفتاح "org" لأنه ده الاسم الحقيقي في الـmetadata.

        info_type مش موجود في الـmetadata schema الحالية، فبيتجاهل هنا بدل ما
        نبني فلتر بمفتاح مش موجود أصلًا (وهيرجع صفر نتائج لو استخدمناه).
        """
        if info_type:
            logger.warning(
                "info_type='%s' اتبعت بس مفيش 'info_type' في الـmetadata الحالية "
                "(org/document/page بس) - هيتجاهل الفلتر ده.",
                info_type,
            )

        if not program_name:
            return {}
        return {"org": program_name}

    @staticmethod
    def _parse_results(raw: dict[str, Any]) -> list[RetrievedChunk]:
        """
        Chroma بترجع distances مش similarity scores، فبنحولها لدرجة تشابه
        تقريبية بين 0 و1 (الأعلى = أقرب) عشان تبقى سهلة القراءة والفلترة.
        """
        documents = (raw.get("documents") or [[]])[0]
        metadatas = (raw.get("metadatas") or [[]])[0]
        distances = (raw.get("distances") or [[]])[0]

        chunks: list[RetrievedChunk] = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            score = 1.0 / (1.0 + dist) if dist is not None else 0.0
            chunks.append(RetrievedChunk(text=doc, score=score, metadata=meta or {}))

        # الأقرب (score أعلى) أولًا
        chunks.sort(key=lambda c: c.score, reverse=True)
        return chunks


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    r = Retriever()
    demo_query = "ايه شروط التقديم في رواد مصر الرقمية؟"
    for item in r.retrieve(demo_query, program_name="depi", top_k=3):
        print(f"[{item['score']:.3f}] {item['metadata']} -> {item['text'][:100]}")