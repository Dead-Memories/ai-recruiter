"""Сквозной пайплайн: вакансия → ранжированная выдача карточек кандидатов."""

from __future__ import annotations

from ai_recruiter.agents import Orchestrator
from ai_recruiter.embeddings import (
    EmbeddingModel,
    VectorStore,
    build_index,
    get_embedder,
    get_store,
    load_manifest,
)
from ai_recruiter.report import build_report
from ai_recruiter.schema import CandidateReport, Vacancy
from ai_recruiter.tools import (
    get_resume_chunks,
    rank_candidates,
    set_search_context,
)


def _manifest_lookup(manifest: list[dict]) -> dict[str, dict]:
    return {e.get("candidate_id", ""): e for e in manifest}


def run_pipeline(
    vacancy: Vacancy,
    top_k: int = 10,
    store: VectorStore | None = None,
    embedder: EmbeddingModel | None = None,
    manifest: list[dict] | None = None,
    orchestrator: Orchestrator | None = None,
    limit: int | None = None,
) -> list[CandidateReport]:
    """Прогоняет полный пайплайн и возвращает ранжированные карточки кандидатов.

    Если `store` не передан, строится свежий индекс по манифесту (парсинг +
    чанкинг + эмбеддинг). Результат отсортирован по итоговому скору.
    """
    manifest = manifest if manifest is not None else load_manifest()
    lookup = _manifest_lookup(manifest)

    if store is None:
        store = build_index(embedder=embedder, manifest=manifest, limit=limit)
    embedder = embedder or get_embedder()
    set_search_context(store=store, embedder=embedder)

    orchestrator = orchestrator or Orchestrator()
    matches = rank_candidates(vacancy.text, top_k=top_k, store=store, embedder=embedder)

    reports: list[CandidateReport] = []
    for match in matches:
        candidate = lookup.get(match.candidate_id)
        if candidate is None:
            continue
        chunks = get_resume_chunks(match.candidate_id, store=store)
        resume_text = "\n".join(c.text for c in chunks)

        agent_results = orchestrator.assess_candidate(vacancy, candidate, resume_text)
        report = build_report(vacancy, candidate, agent_results, match.score)
        reports.append(report)

    reports.sort(key=lambda r: r.score, reverse=True)
    return reports


__all__ = ["run_pipeline"]
