"""Подсчёт коммерческого опыта по датам из текста резюме.

Эвристика двухступенчатая:
1. Явное указание в шапке вида «Опыт работы — 13 лет 1 месяц».
2. Иначе — парсинг диапазонов дат в строках опыта: «08.2020 — 09.2023»,
   «2018–2020», «с 2019 по наст. время» и суммирование длительностей.
"""

from __future__ import annotations

import re

# Текущая дата для диапазонов «наст. время». Согласовано с генератором.
NOW_YEAR, NOW_MONTH = 2025, 8

_EXPLICIT_RE = re.compile(
    r"(?P<years>\d+(?:[.,]\d+)?)\s*(?:лет|года|год|г\.?)\b"
    r"(?:\s*(?P<months>\d+)\s*(?:месяц|мес))?",
    re.IGNORECASE,
)

_RANGE_RE = re.compile(
    r"(?P<start>\d{1,2}\.\d{4}|\d{4})"
    r"\s*(?:—|–|-|по)\s*"
    r"(?P<end>наст\.?\s*время|\d{1,2}\.\d{4}|\d{4})",
    re.IGNORECASE,
)


def _parse_date(token: str, *, is_end: bool) -> tuple[int, int]:
    """Преобразует токен даты в (год, месяц)."""
    token = token.strip().lower()
    if "наст" in token:
        return NOW_YEAR, NOW_MONTH
    if "." in token:
        month, year = token.split(".")
        return int(year), int(month)
    # Голый год без месяца трактуем как середину года (нейтральная оценка).
    return int(token), 6


def _explicit_years(text: str) -> float | None:
    m = _EXPLICIT_RE.search(text)
    if not m:
        return None
    years = float(m.group("years").replace(",", "."))
    months = int(m.group("months")) if m.group("months") else 0
    return round(years + months / 12, 1)


def _sum_ranges(text: str) -> float | None:
    total_months = 0
    found = False
    for m in _RANGE_RE.finditer(text):
        sy, sm = _parse_date(m.group("start"), is_end=False)
        ey, em = _parse_date(m.group("end"), is_end=True)
        months = (ey * 12 + em) - (sy * 12 + sm)
        if months <= 0:
            continue
        total_months += months
        found = True
    if not found:
        return None
    return round(total_months / 12, 1)


def extract_experience_years(text: str) -> float:
    """Оценивает коммерческий опыт в годах. 0.0 при отсутствии данных."""
    if not text:
        return 0.0
    explicit = _explicit_years(text)
    if explicit is not None:
        return explicit
    ranges = _sum_ranges(text)
    return ranges if ranges is not None else 0.0


__all__ = ["extract_experience_years"]
