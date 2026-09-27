"""Общая база для агентов: попытка LLM → fallback на правила.

Каждый агент сначала пробует получить структурированный JSON от LLM; если
модель недоступна или ответ не проходит валидацию, использует детерминированный
rule-based скоринг на основе тулов.
"""

from __future__ import annotations

from ai_recruiter.agents.llm import LLMClient, client
from ai_recruiter.schema import AgentResult, Vacancy


def _clean_text(text: str, limit: int = 6000) -> str:
    return text.strip()[:limit]


def _valid_llm_result(data: dict | None) -> AgentResult | None:
    """Валидирует JSON от LLM. Возвращает AgentResult или None."""
    if not isinstance(data, dict):
        return None
    score = data.get("score")
    if not isinstance(score, (int, float)):
        return None
    score = max(0.0, min(100.0, float(score)))

    def _list(key: str) -> list[str]:
        val = data.get(key, [])
        if not isinstance(val, list):
            return []
        return [str(x) for x in val][:8]

    return AgentResult(
        agent="",
        score=round(score, 1),
        pros=_list("pros"),
        cons=_list("cons"),
        risks=_list("risks"),
    )


def llm_assess(
    llm: LLMClient,
    agent_name: str,
    system: str,
    user: str,
) -> AgentResult | None:
    """Пробует получить результат агента от LLM; None при неудаче."""
    prompt = system + "\n\n" + user
    data = llm.complete_json(prompt)
    result = _valid_llm_result(data)
    if result is None:
        return None
    result.agent = agent_name
    return result


def candidate_resume_text(candidate: dict, resume_text: str) -> str:
    """Собирает связный текст резюме из манифеста и извлечённого текста."""
    return resume_text or candidate.get("summary", "")


__all__ = ["llm_assess", "candidate_resume_text", "_valid_llm_result"]
