"""HR-Аналитик: динамика карьеры, стабильность, софт-скиллы, red flags."""

from __future__ import annotations

import re

from ai_recruiter.agents.base import llm_assess
from ai_recruiter.agents.llm import client
from ai_recruiter.schema import AgentResult, Vacancy

_SYSTEM = (
    "Ты — HR-аналитик. Оцени кандидата по динамике карьеры, стабильности мест "
    "работы, языкам и потенциальным red flags. Верни строгий JSON: "
    '{"score": 0..100, "pros": [..], "cons": [..], "risks": [..]}. '
    "Пиши только на русском."
)

_LEVEL_TO_RANK = {
    "B1": 1, "Intermediate": 2, "B2": 3, "Upper-Intermediate": 3, "C1": 4, "C2": 4,
}


def _segment_years(start: str, end: str) -> float:
    """Длительность одного места работы в годах по датам (MM.YYYY или YYYY)."""
    now_y, now_m = 2025, 8

    def parse(s: str, is_end: bool) -> tuple[int, int]:
        s = s.strip().lower()
        if "наст" in s:
            return now_y, now_m
        if "." in s:
            m, y = s.split(".")
            return int(y), int(m)
        return int(s), (12 if is_end else 1)

    sy, sm = parse(start, False)
    ey, em = parse(end, True)
    months = (ey * 12 + em) - (sy * 12 + sm)
    return max(0.0, months / 12)


def _english_rank(languages: str) -> int:
    if not languages:
        return 0
    best = 0
    for token, rank in _LEVEL_TO_RANK.items():
        if re.search(re.escape(token), languages, re.IGNORECASE):
            best = max(best, rank)
    return best


def _rule_score(candidate: dict) -> tuple[float, dict]:
    experience = candidate.get("experience", []) or []
    tenures = [
        _segment_years(e.get("start", ""), e.get("end", "")) for e in experience
    ]
    n_jobs = len(tenures)
    avg_tenure = sum(tenures) / n_jobs if n_jobs else 0.0

    english = _english_rank(candidate.get("languages", ""))
    years = float(candidate.get("years_experience", 0) or 0)
    seniority = candidate.get("seniority", "middle")

    score = 50.0
    if avg_tenure >= 2.0:
        score += 20
    elif n_jobs >= 3:
        score -= 10  # частые смены мест
    if english >= 3:
        score += 15
    elif english == 2:
        score += 8
    if seniority == "senior" and years >= 5:
        score += 15
    elif seniority == "middle" and years >= 2:
        score += 10

    return round(max(0.0, min(100.0, score)), 1), {
        "n_jobs": n_jobs,
        "avg_tenure": avg_tenure,
        "english": english,
        "years": years,
    }


class HRAnalyst:
    """Оценивает карьерную динамику и HR-риски кандидата."""

    name = "HR-Аналитик"

    def __init__(self, llm=client) -> None:
        self._llm = llm

    def assess(
        self,
        vacancy: Vacancy,
        candidate: dict,
        resume_text: str,
    ) -> AgentResult:
        user = (
            f"Вакансия (грейд: {vacancy.seniority}): {vacancy.title}\n\n"
            f"Кандидат: {candidate.get('full_name', '')} "
            f"({candidate.get('role', '')}, {candidate.get('seniority', '')})\n"
            f"Опыт: {candidate.get('years_experience', 0)} лет\n"
            f"Языки: {candidate.get('languages', '')}\n\n"
            f"Резюме:\n{resume_text[:5000]}"
        )
        result = llm_assess(self._llm, self.name, _SYSTEM, user)
        if result is not None:
            return result
        return self._assess_rules(candidate)

    def _assess_rules(self, candidate: dict) -> AgentResult:
        score, info = _rule_score(candidate)
        pros: list[str] = []
        cons: list[str] = []
        risks: list[str] = []

        if info["n_jobs"] == 0:
            risks.append("Не указан опыт работы")
        elif info["avg_tenure"] >= 2.0:
            pros.append(f"Стабильная карьера: в среднем {info['avg_tenure']:.1f} г/место")
        else:
            cons.append(f"Частая смена мест: {info['n_jobs']} мест, средний срок {info['avg_tenure']:.1f} г")
            risks.append("Риск удержания: короткий средний срок работы на месте")

        if info["english"] >= 3:
            pros.append("Уверенный английский (B2+)")
        elif info["english"] == 0:
            cons.append("Не указан уровень английского")

        if candidate.get("seniority") == "senior" and info["years"] >= 5:
            pros.append("Опыт подтверждает senior-грейд")

        return AgentResult(
            agent=self.name,
            score=score,
            pros=pros,
            cons=cons,
            risks=risks,
        )


__all__ = ["HRAnalyst"]
