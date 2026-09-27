"""Отчёт: карточка кандидата с вердиктом (Markdown/HTML)."""

from ai_recruiter.report.report import (
    HR_WEIGHT,
    SEM_WEIGHT,
    TECH_WEIGHT,
    aggregate,
    build_report,
    render_html,
    render_markdown,
)

__all__ = [
    "TECH_WEIGHT",
    "HR_WEIGHT",
    "SEM_WEIGHT",
    "aggregate",
    "build_report",
    "render_html",
    "render_markdown",
]
