"""Unit-тесты метрик оценки ранжирования."""

from __future__ import annotations

from ai_recruiter.evaluation import (
    EvaluationResult,
    _hit,
    _precision,
    _reciprocal_rank,
    evaluate,
)
from ai_recruiter.schema import CandidateReport


def _report(cid: str, role: str, score: float) -> CandidateReport:
    return CandidateReport(
        candidate_id=cid,
        full_name=cid,
        role=role,
        seniority="middle",
        years_experience=3.0,
        score=score,
        verdict="Рекомендован",
    )


class TestRankingHelpers:
    def test_reciprocal_rank(self):
        reports = [
            _report("a", "Backend", 90),
            _report("b", "QA", 80),
            _report("c", "Backend", 70),
        ]
        assert _reciprocal_rank(reports, "Backend") == 1.0
        assert _reciprocal_rank(reports, "QA") == 0.5
        assert _reciprocal_rank(reports, "DevOps") == 0.0

    def test_hit(self):
        reports = [_report("a", "Backend", 90), _report("b", "QA", 80)]
        assert _hit(reports, "Backend", 1) is True
        assert _hit(reports, "QA", 1) is False
        assert _hit(reports, "QA", 3) is True

    def test_precision(self):
        reports = [_report("a", "Backend", 90), _report("b", "QA", 80)]
        assert _precision(reports, "Backend", 2) == 0.5

    def test_empty(self):
        assert _reciprocal_rank([], "Backend") == 0.0
        assert _precision([], "Backend", 5) == 0.0


class TestEvaluate:
    def test_returns_metrics(self):
        from ai_recruiter.schema import Vacancy

        vacancies = [Vacancy(title="Backend", role="Backend-разработчик (Python)", skills_must=["Python"])]
        result = evaluate(vacancies, top_k=5)
        assert isinstance(result, EvaluationResult)
        assert 0.0 <= result.mrr <= 1.0
        assert len(result.per_vacancy) == 1
