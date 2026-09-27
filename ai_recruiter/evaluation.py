"""Оценка качества ранжирования на ground-truth данных.

Демо-резюме генерируются с известной ролью (`role` в манифесте), поэтому
можно измерить, насколько хорошо семантический поиск поднимает «релевантных»
кандидатов (той же роли, что и вакансия) наверх выдачи.

Метрики:
- MRR — средний обратный ранг первого релевантного кандидата;
- Hit@k — доля вакансий, где релевантный кандидат попал в топ-k;
- Precision@k — доля релевантных среди топ-k.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ai_recruiter.embeddings import EmbeddingModel, VectorStore
from ai_recruiter.pipeline import run_pipeline
from ai_recruiter.schema import CandidateReport, Vacancy


@dataclass
class EvaluationResult:
    """Сводные метрики по набору вакансий."""

    mrr: float
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    precision_at_5: float
    per_vacancy: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "mrr": self.mrr,
            "hit_at_1": self.hit_at_1,
            "hit_at_3": self.hit_at_3,
            "hit_at_5": self.hit_at_5,
            "precision_at_5": self.precision_at_5,
            "per_vacancy": self.per_vacancy,
        }


def _is_relevant(report: CandidateReport, role: str) -> bool:
    if not role:
        return False
    return report.role == role


def _reciprocal_rank(reports: list[CandidateReport], role: str) -> float:
    for rank, report in enumerate(reports, start=1):
        if _is_relevant(report, role):
            return 1.0 / rank
    return 0.0


def _hit(reports: list[CandidateReport], role: str, k: int) -> bool:
    return any(_is_relevant(r, role) for r in reports[:k])


def _precision(reports: list[CandidateReport], role: str, k: int) -> float:
    if not reports:
        return 0.0
    top = reports[:k]
    return sum(1 for r in top if _is_relevant(r, role)) / len(top)


def evaluate(
    vacancies: list[Vacancy],
    top_k: int = 5,
    store: VectorStore | None = None,
    embedder: EmbeddingModel | None = None,
    manifest: list[dict] | None = None,
) -> EvaluationResult:
    """Прогоняет пайплайн по всем вакансиям и считает метрики."""
    rr_sum = 0.0
    hit1 = hit3 = hit5 = 0
    prec_sum = 0.0
    per_vacancy: list[dict] = []

    for vacancy in vacancies:
        reports = run_pipeline(
            vacancy,
            top_k=top_k,
            store=store,
            embedder=embedder,
            manifest=manifest,
        )
        rr = _reciprocal_rank(reports, vacancy.role)
        rr_sum += rr
        hit1 += _hit(reports, vacancy.role, 1)
        hit3 += _hit(reports, vacancy.role, 3)
        hit5 += _hit(reports, vacancy.role, 5)
        prec_sum += _precision(reports, vacancy.role, top_k)

        per_vacancy.append(
            {
                "title": vacancy.title,
                "role": vacancy.role,
                "mrr": rr,
                "top_candidates": [r.full_name for r in reports[:top_k]],
                "top_roles": [r.role for r in reports[:top_k]],
            }
        )

    n = max(len(vacancies), 1)
    return EvaluationResult(
        mrr=round(rr_sum / n, 3),
        hit_at_1=round(hit1 / n, 3),
        hit_at_3=round(hit3 / n, 3),
        hit_at_5=round(hit5 / n, 3),
        precision_at_5=round(prec_sum / n, 3),
        per_vacancy=per_vacancy,
    )


__all__ = ["EvaluationResult", "evaluate"]
