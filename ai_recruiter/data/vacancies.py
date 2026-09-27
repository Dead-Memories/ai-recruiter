"""Генератор тестовых вакансий (JSON в data/vacancies).

Набор из 5 вакансий разной сложности, согласованный с ролями генератора
резюме. Воспроизводимо: фиксированные словари, записываются в JSON.

Запуск:
    python -m ai_recruiter.data.vacancies
"""

from __future__ import annotations

import json
from pathlib import Path

from ai_recruiter.config import config

VACANCIES: list[dict] = [
    {
        "title": "Backend-разработчик Python (Middle+)",
        "role": "Backend-разработчик (Python)",
        "seniority": "middle",
        "requirements": [
            "Разработка и поддержка высоконагруженных REST/gRPC-сервисов на Python",
            "Проектирование схем БД и оптимизация SQL-запросов",
            "Написание автотестов и настройка CI/CD",
        ],
        "skills_must": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "skills_nice": ["Kubernetes", "Redis", "Kafka", "gRPC"],
    },
    {
        "title": "Senior DevOps-инженер",
        "role": "DevOps-инженер",
        "seniority": "senior",
        "requirements": [
            "Автоматизация инфраструктуры (IaC)",
            "Построение CI/CD-пайплайнов",
            "Эксплуатация Kubernetes-кластеров",
        ],
        "skills_must": ["Linux", "Docker", "Kubernetes", "Terraform", "CI/CD"],
        "skills_nice": ["AWS", "Prometheus", "Grafana", "Helm"],
    },
    {
        "title": "QA Automation Engineer (Java/Python)",
        "role": "QA-инженер",
        "seniority": "middle",
        "requirements": [
            "Разработка автотестов API и UI",
            "Ведение тестовой документации",
            "Запуски автотестов в CI",
        ],
        "skills_must": ["Python", "pytest", "Selenium", "REST API"],
        "skills_nice": ["Playwright", "Postman", "Jenkins", "Docker"],
    },
    {
        "title": "ML-инженер (NLP/LLM)",
        "role": "ML-инженер",
        "seniority": "senior",
        "requirements": [
            "Обучение и деплой ML-моделей в продакшн",
            "Построение пайплайнов обработки данных",
            "Тюнинг LLM и построение RAG-систем",
        ],
        "skills_must": ["Python", "PyTorch", "Transformers", "LLM"],
        "skills_nice": ["MLflow", "Docker", "Kubernetes", "ONNX"],
    },
    {
        "title": "Data Analyst (Junior+)",
        "role": "Data Analyst",
        "seniority": "junior",
        "requirements": [
            "Построение дашбордов и отчётности",
            "Проведение A/B-тестов",
            "Написание SQL-запросов",
        ],
        "skills_must": ["SQL", "Python", "Pandas"],
        "skills_nice": ["Tableau", "Airflow", "ClickHouse"],
    },
]


def generate_vacancies(vacancies: list[dict] | None = None) -> list[Path]:
    """Записывает вакансии в data/vacancies и возвращает пути файлов."""
    config.ensure_dirs()
    vacancies = vacancies if vacancies is not None else VACANCIES
    paths: list[Path] = []
    for i, vac in enumerate(vacancies, start=1):
        path = config.vacancies_dir / f"vacancy_{i:02d}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(vac, f, ensure_ascii=False, indent=2)
        paths.append(path)
    return paths


def main() -> None:
    paths = generate_vacancies()
    print(f"Сгенерировано вакансий: {len(paths)}")
    for p in paths:
        print(f"  {p}")


if __name__ == "__main__":
    main()
