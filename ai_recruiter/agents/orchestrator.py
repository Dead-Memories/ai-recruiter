"""Оркестратор агентов: прогон Технического Скринера и HR-Аналитика."""

from __future__ import annotations

from ai_recruiter.agents.hr import HRAnalyst
from ai_recruiter.agents.technical import TechnicalScreener
from ai_recruiter.schema import AgentResult, Vacancy


class Orchestrator:
    """Запускает команду агентов для одного кандидата."""

    def __init__(
        self,
        technical: TechnicalScreener | None = None,
        hr: HRAnalyst | None = None,
    ) -> None:
        self.technical = technical or TechnicalScreener()
        self.hr = hr or HRAnalyst()

    def assess_candidate(
        self,
        vacancy: Vacancy,
        candidate: dict,
        resume_text: str,
    ) -> dict[str, AgentResult]:
        """Возвращает результаты обоих агентов: {'technical': .., 'hr': ..}."""
        technical = self.technical.assess(vacancy, candidate, resume_text)
        hr = self.hr.assess(vacancy, candidate, resume_text)
        return {"technical": technical, "hr": hr}


__all__ = ["Orchestrator"]
