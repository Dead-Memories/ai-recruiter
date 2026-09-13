"""Чанкинг текста резюме по смысловым секциям.

HH.ru и другие выгрузки структурируют резюме по заголовкам: «Опыт работы»,
«Ключевые навыки», «Образование», «О себе» и т. п. (русским или английским).
Модуль находит такие заголовки и нарезает текст на чанки с меткой секции.

Контракт чанка (см. Task3_plan.md §4):
    {section, text}  (+ candidate_id добавляется на этапе индексации).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Канонические секции и их заголовки (русский/английский), нормализованные.
HEADER_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": (
        "about",
        "о себе",
        "обо мне",
        "о себе и опыте",
        "кратко обо мне",
        "summary",
        "profile",
    ),
    "experience": (
        "experience",
        "опыт работы",
        "work experience",
        "employment history",
    ),
    "skills": (
        "skills",
        "key skills",
        "навыки",
        "ключевые навыки",
        "профессиональные навыки",
    ),
    "education": (
        "education",
        "образование",
        "высшее образование",
    ),
    "languages": (
        "languages",
        "языки",
        "знание языков",
        "владение языками",
    ),
    "additional": (
        "additional",
        "дополнительно",
        "дополнительная информация",
    ),
    "certifications": (
        "certifications",
        "сертификаты",
        "курсы",
        "повышение квалификации",
        "courses",
    ),
}

# Секция для блока до первого распознанного заголовка (ФИО, контакты, позиция).
PERSONAL_SECTION = "personal"
# Секция-фолбэк, если заголовков не нашлось.
FULL_SECTION = "full"


@dataclass
class Chunk:
    """Смысловой фрагмент резюме."""

    section: str
    text: str
    candidate_id: str = ""


def _normalize_header(line: str) -> str:
    """Приводит строку-заголовок к каноническому виду."""
    norm = line.strip().lower()
    norm = norm.replace("\u00a0", " ")
    # Отбрасываем суффиксы вида «Опыт работы — 13 лет 1 месяц» / «Skills: ...».
    for sep in ("\u2014", "\u2013", " - ", ":"):
        norm = norm.split(sep)[0].strip()
    norm = re.sub(r"\s+", " ", norm).strip(" -.")
    return norm


def _match_section(line: str) -> str | None:
    """Возвращает каноническую секцию, если строка — заголовок секции."""
    norm = _normalize_header(line)
    if not norm:
        return None
    for section, aliases in HEADER_ALIASES.items():
        if norm in aliases:
            return section
    return None


def _find_boundaries(lines: list[str]) -> list[tuple[int, str]]:
    """Индексы строк-заголовков и их секции в порядке появления."""
    boundaries: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        section = _match_section(line)
        if section is not None:
            boundaries.append((idx, section))
    return boundaries


def chunk_resume(text: str) -> list[Chunk]:
    """Нарезает текст резюме на чанки по секциям.

    Если заголовки не найдены — возвращает один чанк `full`.
    """
    lines = text.split("\n")
    boundaries = _find_boundaries(lines)

    if not boundaries:
        body = text.strip()
        return [Chunk(section=FULL_SECTION, text=body)] if body else []

    chunks: list[Chunk] = []

    # Блок до первого заголовка (ФИО, контакты, желаемая позиция).
    pre = "\n".join(lines[: boundaries[0][0]]).strip()
    if pre:
        chunks.append(Chunk(section=PERSONAL_SECTION, text=pre))

    for k, (start, section) in enumerate(boundaries):
        end = boundaries[k + 1][0] if k + 1 < len(boundaries) else len(lines)
        # Заголовок включаем в текст: «Опыт работы — 13 лет» содержит стаж.
        body = "\n".join(lines[start:end]).strip()
        if body:
            chunks.append(Chunk(section=section, text=body))

    return chunks


def chunk_file(path: str | Path) -> list[Chunk]:
    """Парсит файл и нарезает его текст на чанки."""
    from ai_recruiter.parsing import extract_text

    return chunk_resume(extract_text(path))


__all__ = [
    "HEADER_ALIASES",
    "PERSONAL_SECTION",
    "FULL_SECTION",
    "Chunk",
    "chunk_resume",
    "chunk_file",
]
