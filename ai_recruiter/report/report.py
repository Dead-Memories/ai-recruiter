"""Генератор отчёта: агрегация скора и карточка кандидата (.md/.html)."""

from __future__ import annotations

from ai_recruiter.schema import (
    VERDICT_RECOMMENDED,
    VERDICT_REJECT,
    VERDICT_RESERVE,
    AgentResult,
    CandidateReport,
    Vacancy,
)

TECH_WEIGHT = 0.5
HR_WEIGHT = 0.3
SEM_WEIGHT = 0.2


def aggregate(
    technical: AgentResult,
    hr: AgentResult,
    semantic_score: float,
) -> tuple[float, str]:
    """Считает взвешенный скор (0..100) и вердикт."""
    sem = max(0.0, min(1.0, semantic_score)) * 100
    score = TECH_WEIGHT * technical.score + HR_WEIGHT * hr.score + SEM_WEIGHT * sem

    if score >= 75:
        verdict = VERDICT_RECOMMENDED
    elif score >= 50:
        verdict = VERDICT_RESERVE
    else:
        verdict = VERDICT_REJECT

    return round(score, 1), verdict


def build_report(
    vacancy: Vacancy,
    candidate: dict,
    agent_results: dict[str, AgentResult],
    semantic_score: float,
) -> CandidateReport:
    """Собирает итоговую карточку кандидата."""
    technical = agent_results["technical"]
    hr = agent_results["hr"]
    score, verdict = aggregate(technical, hr, semantic_score)

    pros = technical.pros + hr.pros
    cons = technical.cons + hr.cons
    risks = technical.risks + hr.risks

    return CandidateReport(
        candidate_id=candidate.get("candidate_id", ""),
        full_name=candidate.get("full_name", ""),
        role=candidate.get("role", ""),
        seniority=candidate.get("seniority", ""),
        years_experience=float(candidate.get("years_experience", 0) or 0),
        score=score,
        verdict=verdict,
        pros=pros,
        cons=cons,
        risks=risks,
        technical_score=technical.score,
        hr_score=hr.score,
        semantic_score=round(max(0.0, min(1.0, semantic_score)) * 100, 1),
    )


def _bullet(items: list[str]) -> str:
    if not items:
        return "-"
    return "\n".join(f"- {i}" for i in items)


def render_markdown(report: CandidateReport) -> str:
    """Карточка кандидата в Markdown."""
    return (
        f"## {report.full_name} — {report.score}% ({report.verdict})\n\n"
        f"- Роль: {report.role} ({report.seniority})\n"
        f"- Опыт: {report.years_experience:.1f} лет\n"
        f"- Технический скор: {report.technical_score} | "
        f"HR: {report.hr_score} | Семантический: {report.semantic_score}\n\n"
        f"### Плюсы\n{_bullet(report.pros)}\n\n"
        f"### Минусы\n{_bullet(report.cons)}\n\n"
        f"### Риски\n{_bullet(report.risks)}\n"
    )


def render_html(report: CandidateReport) -> str:
    """Карточка кандидата в HTML."""
    esc = lambda s: (  # noqa: E731
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    pros = "".join(f"<li>{esc(p)}</li>" for p in report.pros) or "<li>—</li>"
    cons = "".join(f"<li>{esc(c)}</li>" for c in report.cons) or "<li>—</li>"
    risks = "".join(f"<li>{esc(r)}</li>" for r in report.risks) or "<li>—</li>"
    return (
        f'<div class="card" style="border:1px solid #ccc;border-radius:8px;'
        f'padding:16px;margin:12px 0;font-family:sans-serif;">'
        f"<h2>{esc(report.full_name)} — {report.score}% "
        f"({esc(report.verdict)})</h2>"
        f"<p><b>Роль:</b> {esc(report.role)} ({esc(report.seniority)})<br>"
        f"<b>Опыт:</b> {report.years_experience:.1f} лет<br>"
        f"<b>Тех:</b> {report.technical_score} | <b>HR:</b> {report.hr_score} | "
        f"<b>Семантика:</b> {report.semantic_score}</p>"
        f"<h3>Плюсы</h3><ul>{pros}</ul>"
        f"<h3>Минусы</h3><ul>{cons}</ul>"
        f"<h3>Риски</h3><ul>{risks}</ul></div>"
    )


__all__ = [
    "TECH_WEIGHT",
    "HR_WEIGHT",
    "SEM_WEIGHT",
    "aggregate",
    "build_report",
    "render_markdown",
    "render_html",
]
