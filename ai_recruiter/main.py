"""CLI: запуск пайплайна «вакансия → ранжированная выдача».

Примеры:
    python -m ai_recruiter.main --vacancy data/vacancies/vacancy_01.json --top-k 5
    python -m ai_recruiter.main --vacancy data/vacancies/vacancy_01.json --format html
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ai_recruiter.pipeline import run_pipeline
from ai_recruiter.report import render_html, render_markdown
from ai_recruiter.schema import Vacancy


def main() -> None:
    parser = argparse.ArgumentParser(description="AI-Recruiter: ранжирование кандидатов")
    parser.add_argument("--vacancy", required=True, help="Путь к JSON-вакансии")
    parser.add_argument("--top-k", type=int, default=5, help="Число кандидатов в выдаче")
    parser.add_argument("--format", choices=["md", "html"], default="md")
    args = parser.parse_args()

    vacancy = Vacancy.load(args.vacancy)
    reports = run_pipeline(vacancy, top_k=args.top_k)

    if not reports:
        print("Кандидаты не найдены. Проверьте, что индекс построен.")
        return

    print(f"Вакансия: {vacancy.title}\n")
    for report in reports:
        text = render_html(report) if args.format == "html" else render_markdown(report)
        print(text)


if __name__ == "__main__":
    main()
