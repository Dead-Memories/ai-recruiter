"""Unit-тесты агентов (rule-based путь, без LLM)."""

from __future__ import annotations

from ai_recruiter.agents import HRAnalyst, Orchestrator, TechnicalScreener
from ai_recruiter.schema import Vacancy

VACANCY = Vacancy(
    title="Backend Python",
    requirements=["Разработка сервисов на Python"],
    skills_must=["Python", "FastAPI", "PostgreSQL"],
    skills_nice=["Docker", "Kubernetes"],
    seniority="middle",
)

CANDIDATE = {
    "candidate_id": "cand_0001",
    "full_name": "Иванов Иван Иванович",
    "role": "Backend-разработчик (Python)",
    "seniority": "middle",
    "years_experience": 3.5,
    "skills": ["Python", "Django", "PostgreSQL", "Docker"],
    "languages": "Русский — родной, английский — B2",
    "experience": [
        {"start": "08.2021", "end": "наст. время", "company": "Яндекс"},
        {"start": "01.2019", "end": "07.2021", "company": "Сбер"},
    ],
}

RESUME_TEXT = (
    "Иванов Иван\nОпыт работы — 3 года 6 месяцев\n"
    "Яндекс 08.2021 — наст. время\nРазрабатывал сервисы на Python FastAPI PostgreSQL Docker\n"
    "Ключевые навыки\nPython FastAPI PostgreSQL Docker Git"
)


class TestTechnicalScreener:
    def test_high_match(self):
        result = TechnicalScreener().assess(VACANCY, CANDIDATE, RESUME_TEXT)
        assert result.agent == "Технический Скринер"
        assert result.score >= 80
        assert any("FastAPI" in p for p in result.pros)

    def test_missing_mandatory_skills(self):
        vacancy = Vacancy(
            title="Go backend",
            skills_must=["Go", "gRPC"],
            seniority="middle",
        )
        result = TechnicalScreener().assess(vacancy, CANDIDATE, RESUME_TEXT)
        assert result.score < 50
        assert result.cons
        assert result.risks


class TestHRAnalyst:
    def test_stable_career(self):
        result = HRAnalyst().assess(VACANCY, CANDIDATE, RESUME_TEXT)
        assert result.agent == "HR-Аналитик"
        assert result.score >= 70

    def test_job_hopper_flagged(self):
        candidate = {
            **CANDIDATE,
            "experience": [
                {"start": "01.2024", "end": "наст. время", "company": "A"},
                {"start": "01.2023", "end": "12.2023", "company": "B"},
                {"start": "01.2022", "end": "12.2022", "company": "C"},
            ],
        }
        result = HRAnalyst().assess(VACANCY, candidate, RESUME_TEXT)
        assert any("смена" in r or "удержани" in r for r in result.risks)


class TestOrchestrator:
    def test_returns_both_agents(self):
        results = Orchestrator().assess_candidate(VACANCY, CANDIDATE, RESUME_TEXT)
        assert set(results) == {"technical", "hr"}
        assert results["technical"].agent == "Технический Скринер"
        assert results["hr"].agent == "HR-Аналитик"
