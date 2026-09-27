"""Векторное хранилище чанков резюме.

Основной бэкенд — ChromaDB (локальная персистентная коллекция). Если
`chromadb` не установлен, прозрачно используется простой in-memory бэкенд
на чистом Python (список векторов + косинусная близость), чтобы пайплайн
и тесты работали без тяжёлых зависимостей.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass

from ai_recruiter.config import config

_CHROMA_AVAILABLE = importlib.util.find_spec("chromadb") is not None


@dataclass
class SearchResult:
    """Результат поиска по одному чанку."""

    candidate_id: str
    section: str
    text: str
    score: float


class VectorStore:
    """Интерфейс хранилища: добавить чанк, искать по вектору, получить кандидата."""

    def add(
        self,
        candidate_id: str,
        section: str,
        text: str,
        embedding: list[float],
    ) -> None:
        raise NotImplementedError

    def query(self, embedding: list[float], top_k: int = 10) -> list[SearchResult]:
        raise NotImplementedError

    def get_candidate(self, candidate_id: str) -> list[SearchResult]:
        raise NotImplementedError

    def count(self) -> int:
        raise NotImplementedError

    def reset(self) -> None:
        raise NotImplementedError


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class InMemoryVectorStore(VectorStore):
    """Fallback: хранение в памяти, косинусная близость на чистом Python."""

    def __init__(self) -> None:
        self._rows: list[tuple[str, str, str, list[float]]] = []

    def add(
        self,
        candidate_id: str,
        section: str,
        text: str,
        embedding: list[float],
    ) -> None:
        self._rows.append((candidate_id, section, text, embedding))

    def query(self, embedding: list[float], top_k: int = 10) -> list[SearchResult]:
        scored = [
            SearchResult(cid, sec, text, _cosine(embedding, vec))
            for cid, sec, text, vec in self._rows
        ]
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]

    def get_candidate(self, candidate_id: str) -> list[SearchResult]:
        return [
            SearchResult(cid, sec, text, 1.0)
            for cid, sec, text, _ in self._rows
            if cid == candidate_id
        ]

    def count(self) -> int:
        return len(self._rows)

    def reset(self) -> None:
        self._rows.clear()


class ChromaVectorStore(VectorStore):
    """ChromaDB-бэкенд с персистентной коллекцией."""

    COLLECTION_NAME = "resume_chunks"

    def __init__(self, persist_dir: str | None = None) -> None:
        import chromadb

        self._client = chromadb.PersistentClient(path=persist_dir or str(config.chroma_dir))
        try:
            self._collection = self._client.get_collection(self.COLLECTION_NAME)
        except Exception:  # noqa: BLE001 — коллекции ещё нет
            self._collection = self._client.create_collection(self.COLLECTION_NAME)

    def add(
        self,
        candidate_id: str,
        section: str,
        text: str,
        embedding: list[float],
    ) -> None:
        doc_id = f"{candidate_id}:{section}"
        self._collection.upsert(
            ids=[doc_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[{"candidate_id": candidate_id, "section": section}],
        )

    def query(self, embedding: list[float], top_k: int = 10) -> list[SearchResult]:
        res = self._collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        results: list[SearchResult] = []
        ids = res["ids"][0]
        documents = res["documents"][0]
        metadatas = res["metadatas"][0]
        distances = res["distances"][0]
        for doc_id, text, meta, dist in zip(ids, documents, metadatas, distances):
            results.append(
                SearchResult(
                    candidate_id=meta["candidate_id"],
                    section=meta["section"],
                    text=text,
                    score=1.0 - float(dist),
                )
            )
        return results

    def get_candidate(self, candidate_id: str) -> list[SearchResult]:
        res = self._collection.get(
            where={"candidate_id": candidate_id},
            include=["documents", "metadatas"],
        )
        return [
            SearchResult(
                candidate_id=meta["candidate_id"],
                section=meta["section"],
                text=text,
                score=1.0,
            )
            for text, meta in zip(res["documents"], res["metadatas"])
        ]

    def count(self) -> int:
        return self._collection.count()

    def reset(self) -> None:
        try:
            self._client.delete_collection(self.COLLECTION_NAME)
        except Exception:  # noqa: BLE001
            pass
        self._collection = self._client.create_collection(self.COLLECTION_NAME)


def get_store() -> VectorStore:
    """Возвращает хранилище: ChromaDB, если доступен, иначе in-memory."""
    if _CHROMA_AVAILABLE:
        return ChromaVectorStore()
    return InMemoryVectorStore()


__all__ = [
    "SearchResult",
    "VectorStore",
    "InMemoryVectorStore",
    "ChromaVectorStore",
    "get_store",
]
