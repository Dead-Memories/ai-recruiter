"""Данные: воспроизводимый генератор демо-резюме и тестовых вакансий."""

from ai_recruiter.data.generator import Candidate, generate, generate_candidate
from ai_recruiter.data.vacancies import VACANCIES, generate_vacancies

__all__ = [
    "Candidate",
    "generate",
    "generate_candidate",
    "VACANCIES",
    "generate_vacancies",
]
