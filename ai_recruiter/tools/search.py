"""Семантический поиск по базе резюме.

`semantic_search` возвращает топ-K чанков по косинусной близости к запросу
(обычно тексту вакансии). `rank_candidates` агрегирует чанки до уровня
кандидата, чтобы получить ранжированный список кандидатов.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ai_recruiter.embeddings import EmbeddingModel, SearchResult, VectorStore
from ai_recruiter.tools.context import get_search_context


@dataclass
class CandidateMatch:
    """Кандидат с агрегированным скором и ссылками на лучшие чанки."""

    candidate_id: str
    score: float
    top_chunks: list[SearchResult] = field(default_factory=list)


def semantic_search(
    query: str,
    top_k: int = 10,
    store: VectorStore | None = None,
    embedder: EmbeddingModel | None = None,
) -> list[SearchResult]:
    """Возвращает топ-K чанков, релевантных запросу."""
    if not query.strip():
        return []
    store, embedder = store, embedder
    if store is None or embedder is None:
        store, embedder = get_search_context()
    vec = embedder.encode([query], is_query=True)[0]
    return store.query(vec, top_k=top_k)


def get_resume_chunks(
    candidate_id: str,
    store: VectorStore | None = None,
) -> list[SearchResult]:
    """Возвращает все чанки кандидата из хранилища."""
    if store is None:
        store, _ = get_search_context()
    return store.get_candidate(candidate_id)


def rank_candidates(
    query: str,
    top_k: int = 20,
    store: VectorStore | None = None,
    embedder: EmbeddingModel | None = None,
) -> list[CandidateMatch]:
    """Ранжирует кандидатов по релевантности запросу.

    Скор кандидата — максимум по его чанкам (плюс небольшой бонус за число
    релевантных секций), чтобы сильный сигнал в одной секции не терялся.
    """
    chunks = semantic_search(query, top_k=top_k * 5, store=store, embedder=embedder)

    by_candidate: dict[str, list[SearchResult]] = {}
    for chunk in chunks:
        by_candidate.setdefault(chunk.candidate_id, []).append(chunk)

    matches: list[CandidateMatch] = []
    for candidate_id, hits in by_candidate.items():
        best = max(c.score for c in hits)
        # Бонус за покрытие нескольких секций (0..0.1).
        bonus = min(len({c.section for c in hits}) - 1, 2) * 0.05
        matches.append(
            CandidateMatch(
                candidate_id=candidate_id,
                score=round(best + bonus, 4),
                top_chunks=sorted(hits, key=lambda c: c.score, reverse=True)[:3],
            )
        )

    matches.sort(key=lambda m: m.score, reverse=True)
    return matches[:top_k]


__all__ = [
    "CandidateMatch",
    "semantic_search",
    "get_resume_chunks",
    "rank_candidates",
]
