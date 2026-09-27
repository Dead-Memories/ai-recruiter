"""Контракты данных (см. Task3_plan.md §4).

Вакансия, результат агента и итоговая карточка кандидата — единый источник
истины для оркестратора, отчёта и пайплайна.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

SENIORITY_LEVELS = {"junior": 1, "middle": 2, "senior": 3}
SENIORITY_MIN_YEARS = {"junior": 0.5, "middle": 2.0, "senior": 5.0}

VERDICT_RECOMMENDED = "Рекомендован"
VERDICT_RESERVE = "В резерв"
VERDICT_REJECT = "Отказ"


@dataclass
class Vacancy:
    """Вакансия: заголовок, требования и навыки."""

    title: str
    requirements: list[str] = field(default_factory=list)
    skills_must: list[str] = field(default_factory=list)
    skills_nice: list[str] = field(default_factory=list)
    seniority: str = "middle"
    role: str = ""

    @property
    def text(self) -> str:
        parts = [self.title]
        if self.requirements:
            parts.append("Требования:\n" + "\n".join(f"- {r}" for r in self.requirements))
        if self.skills_must:
            parts.append("Обязательные навыки: " + ", ".join(self.skills_must))
        if self.skills_nice:
            parts.append("Желательные навыки: " + ", ".join(self.skills_nice))
        parts.append(f"Грейд: {self.seniority}")
        return "\n".join(parts)

    @classmethod
    def from_dict(cls, d: dict) -> "Vacancy":
        return cls(
            title=d.get("title", ""),
            requirements=list(d.get("requirements", [])),
            skills_must=list(d.get("skills_must", [])),
            skills_nice=list(d.get("skills_nice", [])),
            seniority=d.get("seniority", "middle"),
            role=d.get("role", ""),
        )

    @classmethod
    def load(cls, path: str | Path) -> "Vacancy":
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


@dataclass
class AgentResult:
    """Структурированный результат одного агента."""

    agent: str
    score: float  # 0..100
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CandidateReport:
    """Итоговая карточка кандидата."""

    candidate_id: str
    full_name: str
    role: str
    seniority: str
    years_experience: float
    score: float  # 0..100
    verdict: str
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    technical_score: float = 0.0
    hr_score: float = 0.0
    semantic_score: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


__all__ = [
    "SENIORITY_LEVELS",
    "SENIORITY_MIN_YEARS",
    "VERDICT_RECOMMENDED",
    "VERDICT_RESERVE",
    "VERDICT_REJECT",
    "Vacancy",
    "AgentResult",
    "CandidateReport",
]
