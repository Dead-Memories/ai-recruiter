"""Технический Скринер: сопоставляет стек и хард-скиллы с вакансией."""

from __future__ import annotations

from ai_recruiter.agents.base import llm_assess
from ai_recruiter.agents.llm import client
from ai_recruiter.schema import (
    SENIORITY_LEVELS,
    SENIORITY_MIN_YEARS,
    AgentResult,
    Vacancy,
)
from ai_recruiter.tools import check_mandatory_skills, extract_experience_years

_SYSTEM = (
    "Ты — технический скринер. Оцени соответствие кандидата вакансии по стеку, "
    "хард-скиллам и грейду. Верни строгий JSON: "
    '{"score": 0..100, "pros": [..], "cons": [..], "risks": [..]}. '
    "Пиши только на русском. Списки — короткие пункты."
)


def _rule_score(
    vacancy: Vacancy,
    candidate: dict,
    resume_text: str,
) -> tuple[float, dict]:
    must = check_mandatory_skills(resume_text, vacancy.skills_must)
    nice = check_mandatory_skills(resume_text, vacancy.skills_nice)

    cand_sen = SENIORITY_LEVELS.get(candidate.get("seniority", "middle"), 2)
    req_sen = SENIORITY_LEVELS.get(vacancy.seniority, 2)
    sen_match = 1.0 if cand_sen >= req_sen else 0.5

    years = extract_experience_years(resume_text)
    if years <= 0:
        years = float(candidate.get("years_experience", 0) or 0)
    min_years = SENIORITY_MIN_YEARS.get(vacancy.seniority, 2.0)
    years_match = min(1.0, years / max(min_years, 0.01))

    # Взвешенная сумма с нормализацией: желательные навыки учитываются,
    # только если они заданы в вакансии.
    parts = [0.55 * must["ratio"]]
    weight = 0.55
    if vacancy.skills_nice:
        parts.append(0.15 * nice["ratio"])
        weight += 0.15
    parts.append(0.15 * sen_match)
    parts.append(0.15 * years_match)
    weight += 0.30

    score = 100 * (sum(parts) / weight)
    return round(score, 1), {
        "must": must,
        "nice": nice,
        "sen_match": sen_match,
        "years": years,
        "years_match": years_match,
    }


class TechnicalScreener:
    """Оценивает техническое соответствие кандидата вакансии."""

    name = "Технический Скринер"

    def __init__(self, llm=client) -> None:
        self._llm = llm

    def assess(
        self,
        vacancy: Vacancy,
        candidate: dict,
        resume_text: str,
    ) -> AgentResult:
        user = (
            f"Вакансия:\n{vacancy.text}\n\n"
            f"Кандидат: {candidate.get('full_name', '')} "
            f"({candidate.get('role', '')}, {candidate.get('seniority', '')})\n\n"
            f"Резюме:\n{resume_text[:5000]}"
        )
        result = llm_assess(self._llm, self.name, _SYSTEM, user)
        if result is not None:
            return result
        return self._assess_rules(vacancy, candidate, resume_text)

    def _assess_rules(
        self,
        vacancy: Vacancy,
        candidate: dict,
        resume_text: str,
    ) -> AgentResult:
        score, info = _rule_score(vacancy, candidate, resume_text)
        must, nice = info["must"], info["nice"]
        pros: list[str] = []
        cons: list[str] = []
        risks: list[str] = []

        if must["found"]:
            pros.append("Обязательные навыки покрыты: " + ", ".join(must["found"]))
        if must["missing"]:
            cons.append("Нет обязательных навыков: " + ", ".join(must["missing"]))
        if nice["found"]:
            pros.append("Есть желательные навыки: " + ", ".join(nice["found"]))

        if info["years_match"] >= 1.0:
            pros.append(f"Опыт {info['years']:.1f} лет соответствует грейду")
        else:
            cons.append(
                f"Опыт {info['years']:.1f} лет ниже ожиданий для грейда"
            )
        if info["sen_match"] < 1.0:
            cons.append("Грейд кандидата ниже требуемого")

        if must["missing"]:
            risks.append("Ключевые технологии отсутствуют в резюме")
        if not must["found"] and not must["missing"]:
            risks.append("Навыки не удалось проверить по тексту резюме")

        return AgentResult(
            agent=self.name,
            score=score,
            pros=pros,
            cons=cons,
            risks=risks,
        )


__all__ = ["TechnicalScreener"]
