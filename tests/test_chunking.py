"""Unit-тесты модуля чанкинга."""

from __future__ import annotations

from ai_recruiter.chunking import (
    FULL_SECTION,
    PERSONAL_SECTION,
    chunk_resume,
)

RU_RESUME = """\
QA Automation Engineer (Сбер)
Москва, готов к командировкам

Опыт работы — 13 лет 1 месяц
Яндекс
Разрабатывал автотесты на Java.

Ключевые навыки
Java
Selenium

Образование
МГУ, Бакалавр, 2012

Знание языков
Английский — B2
"""

EN_RESUME = """\
QA Automation Engineer
Moscow

EXPERIENCE
Sberbank
Automation tests in Java.

SKILLS
Java
JUnit

ABOUT
5 years in QA.

EDUCATION
MSU

LANGUAGES
English — C1
"""


def test_sections_detected_ru():
    chunks = chunk_resume(RU_RESUME)
    sections = [c.section for c in chunks]
    assert sections == ["personal", "experience", "skills", "education", "languages"]
    assert "13 лет 1 месяц" in chunks[1].text
    assert "Java" in chunks[2].text


def test_sections_detected_en():
    chunks = chunk_resume(EN_RESUME)
    sections = [c.section for c in chunks]
    assert sections == ["personal", "experience", "skills", "summary", "education", "languages"]


def test_personal_block_first():
    chunks = chunk_resume(RU_RESUME)
    assert chunks[0].section == PERSONAL_SECTION
    assert "Москва" in chunks[0].text


def test_fallback_single_chunk():
    text = "Просто текст без заголовков.\nВторая строка."
    chunks = chunk_resume(text)
    assert len(chunks) == 1
    assert chunks[0].section == FULL_SECTION


def test_empty_input():
    assert chunk_resume("") == []
    assert chunk_resume("   \n  ") == []


def test_subheader_not_treated_as_section():
    text = (
        "Опыт работы\n"
        "Стек: Java\n"
        "Достижения:\n"
        "Навыки\n"
        "SQL\n"
    )
    chunks = chunk_resume(text)
    assert [c.section for c in chunks] == ["experience", "skills"]
