"""Unit-тесты модуля отчёта."""

from __future__ import annotations

from ai_recruiter.report import aggregate, build_report, render_html, render_markdown
from ai_recruiter.schema import (
    VERDICT_RECOMMENDED,
    VERDICT_REJECT,
    VERDICT_RESERVE,
    AgentResult,
    Vacancy,
)

VACANCY = Vacancy(title="Backend Python", skills_must=["Python"], seniority="middle")

CANDIDATE = {
    "candidate_id": "cand_0001",
    "full_name": "Иванов Иван",
    "role": "Backend-разработчик (Python)",
    "seniority": "middle",
    "years_experience": 3.5,
}


def _agents(tech=90.0, hr=80.0):
    return {
        "technical": AgentResult(agent="Технический Скринер", score=tech, pros=["+t"], cons=[], risks=[]),
        "hr": AgentResult(agent="HR-Аналитик", score=hr, pros=[], cons=["-h"], risks=["r"]),
    }


class TestAggregate:
    def test_recommended(self):
        score, verdict = aggregate(*(list(_agents().values()) + [0.8]))
        assert score >= 75
        assert verdict == VERDICT_RECOMMENDED

    def test_reserve(self):
        score, verdict = aggregate(*(list(_agents(tech=60, hr=50).values()) + [0.4]))
        assert VERDICT_RESERVE == verdict

    def test_reject(self):
        score, verdict = aggregate(*(list(_agents(tech=20, hr=20).values()) + [0.1]))
        assert verdict == VERDICT_REJECT


class TestBuildReport:
    def test_fields(self):
        report = build_report(VACANCY, CANDIDATE, _agents(), 0.8)
        assert report.candidate_id == "cand_0001"
        assert report.verdict == VERDICT_RECOMMENDED
        assert report.technical_score == 90.0
        assert report.hr_score == 80.0
        assert report.pros == ["+t"]
        assert report.cons == ["-h"]
        assert report.risks == ["r"]


class TestRender:
    def test_markdown_contains_name_and_score(self):
        report = build_report(VACANCY, CANDIDATE, _agents(), 0.8)
        md = render_markdown(report)
        assert "Иванов Иван" in md
        assert "%" in md

    def test_html_escapes(self):
        report = build_report(VACANCY, CANDIDATE, _agents(), 0.8)
        report.full_name = "A <B> & C"
        html = render_html(report)
        assert "A &lt;B&gt; &amp; C" in html
