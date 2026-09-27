"""Проверка наличия обязательных навыков в тексте резюме.

Поиск регистронезависимый; для коротких навыков (≤2 символа, например «Go»)
используются границы слова, чтобы не ловить «Google» / «Django».
"""

from __future__ import annotations

import re


def _skill_present(text_lower: str, skill: str) -> bool:
    s = skill.strip().lower()
    if not s:
        return False
    if len(s) <= 2:
        return re.search(rf"\b{re.escape(s)}\b", text_lower) is not None
    return s in text_lower


def check_mandatory_skills(text: str, skills: list[str]) -> dict:
    """Возвращает найденные/пропущенные навыки и долю покрытия."""
    if not skills:
        return {"found": [], "missing": [], "matched": 0, "total": 0, "ratio": 1.0}

    text_lower = text.lower()
    found: list[str] = []
    missing: list[str] = []
    for skill in skills:
        (found if _skill_present(text_lower, skill) else missing).append(skill)

    total = len(skills)
    return {
        "found": found,
        "missing": missing,
        "matched": len(found),
        "total": total,
        "ratio": len(found) / total,
    }


__all__ = ["check_mandatory_skills"]
