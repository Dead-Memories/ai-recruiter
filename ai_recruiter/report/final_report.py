"""Итоговый отчёт проекта: метрики + примеры карточек (HTML и PDF).

Запуск:
    python -m ai_recruiter.report.final_report

Считает метрики ранжирования (MRR / Hit@k / Precision@k) на демо-данных и
сохраняет отчёт в HTML (всегда) и PDF (если найден TTF-шрифт с кириллицей).
"""

from __future__ import annotations

import json
from pathlib import Path

from ai_recruiter.config import config
from ai_recruiter.embeddings import build_index, load_manifest
from ai_recruiter.evaluation import evaluate
from ai_recruiter.pipeline import run_pipeline
from ai_recruiter.report import render_html
from ai_recruiter.schema import Vacancy


def load_all_vacancies(vacancies_dir: str | Path | None = None) -> list[Vacancy]:
    """Загружает все JSON-вакансии из data/vacancies."""
    directory = Path(vacancies_dir or config.vacancies_dir)
    return [
        Vacancy.load(p)
        for p in sorted(directory.glob("*.json"))
    ]


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _metrics_table(result) -> str:
    rows = (
        ("MRR", f"{result.mrr:.3f}"),
        ("Hit@1", f"{result.hit_at_1:.3f}"),
        ("Hit@3", f"{result.hit_at_3:.3f}"),
        ("Hit@5", f"{result.hit_at_5:.3f}"),
        ("Precision@5", f"{result.precision_at_5:.3f}"),
    )
    return "".join(f"<tr><td>{name}</td><td><b>{value}</b></td></tr>" for name, value in rows)


def _vacancy_rows(per_vacancy: list[dict]) -> str:
    rows = []
    for item in per_vacancy:
        rows.append(
            f"<tr><td>{_esc(item['title'])}</td><td>{_esc(item['role'])}</td>"
            f"<td>{item['mrr']:.3f}</td><td>{_esc(', '.join(item['top_roles'][:3]))}</td></tr>"
        )
    return "".join(rows)


def build_html_report(vacancies: list[Vacancy], result, sample_cards: list[str]) -> str:
    """Собирает HTML-отчёт."""
    return f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<title>AI-Recruiter — итоговый отчёт</title>
<style>
body {{ font-family: -apple-system, Segoe UI, sans-serif; margin: 32px; color: #222; }}
h1, h2 {{ border-bottom: 1px solid #ddd; padding-bottom: 4px; }}
table {{ border-collapse: collapse; margin: 12px 0; }}
td, th {{ border: 1px solid #ccc; padding: 6px 12px; text-align: left; }}
th {{ background: #f4f4f4; }}
.metrics td:first-child {{ font-weight: bold; }}
.card {{ border: 1px solid #ccc; border-radius: 8px; padding: 16px; margin: 12px 0; }}
</style></head><body>
<h1>AI-Recruiter — итоговый отчёт</h1>
<p>Мультиагентная система семантического ранжирования и скоринга кандидатов.</p>

<h2>Метрики ранжирования</h2>
<p>Оценка на демо-данных ({len(result.per_vacancy)} вакансий)
с известным ground-truth (роль кандидата в манифесте).</p>
<table class="metrics">
<tr><th>Метрика</th><th>Значение</th></tr>
{_metrics_table(result)}
</table>

<h2>Разбивка по вакансиям</h2>
<table>
<tr><th>Вакансия</th><th>Целевая роль</th><th>MRR</th><th>Топ-3 роли в выдаче</th></tr>
{_vacancy_rows(result.per_vacancy)}
</table>

<h2>Примеры карточек кандидатов</h2>
{''.join(sample_cards)}
</body></html>"""


def generate_final_report(
    vacancies: list[Vacancy] | None = None,
    top_k: int = 5,
    out_html: str | Path | None = None,
    out_pdf: str | Path | None = None,
) -> dict:
    """Генерирует итоговый отчёт (HTML + PDF) и возвращает пути и метрики."""
    vacancies = vacancies if vacancies is not None else load_all_vacancies()
    manifest = load_manifest()
    store = build_index(manifest=manifest)

    result = evaluate(vacancies, top_k=top_k, store=store, manifest=manifest)

    sample_cards: list[str] = []
    for vacancy in vacancies[:2]:
        reports = run_pipeline(vacancy, top_k=top_k, store=store, manifest=manifest)
        for report in reports[:1]:
            sample_cards.append(render_html(report))

    html = build_html_report(vacancies, result, sample_cards)

    out_html = Path(out_html or config.data_dir / "final_report.html")
    out_html.write_text(html, encoding="utf-8")

    paths = {"html": str(out_html), "pdf": None}
    if out_pdf:
        pdf_path = Path(out_pdf)
        _render_pdf(html, vacancies, result, pdf_path)
        paths["pdf"] = str(pdf_path)

    return {"paths": paths, "metrics": result.to_dict()}


def _render_pdf(html: str, vacancies: list[Vacancy], result, pdf_path: Path) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    from ai_recruiter.data.generator import _find_cyrillic_font

    font_path = _find_cyrillic_font()
    if font_path is None:
        raise RuntimeError("Не найден TTF-шрифт с кириллицей для PDF.")

    pdfmetrics.registerFont(TTFont("Cyr", font_path))
    normal = ParagraphStyle("normal", fontName="Cyr", fontSize=10, leading=14)
    heading = ParagraphStyle("heading", fontName="Cyr", fontSize=16, leading=20, spaceAfter=8)
    sub = ParagraphStyle("sub", fontName="Cyr", fontSize=12, leading=16, spaceBefore=8, spaceAfter=4)

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm)
    story = [Paragraph("AI-Recruiter — итоговый отчёт", heading)]

    story.append(Paragraph("Метрики ранжирования", sub))
    for name, value in (
        ("MRR", result.mrr), ("Hit@1", result.hit_at_1), ("Hit@3", result.hit_at_3),
        ("Hit@5", result.hit_at_5), ("Precision@5", result.precision_at_5),
    ):
        story.append(Paragraph(f"• {name}: <b>{value:.3f}</b>", normal))

    story.append(Paragraph("Разбивка по вакансиям", sub))
    for item in result.per_vacancy:
        story.append(
            Paragraph(
                f"• {item['title']} [{item['role']}] — MRR {item['mrr']:.3f}, "
                f"топ роли: {', '.join(item['top_roles'][:3])}",
                normal,
            )
        )

    story.append(Spacer(1, 8))
    doc.build(story)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Генерация итогового отчёта")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--out-html", type=str, default=None)
    parser.add_argument("--out-pdf", type=str, default=None)
    args = parser.parse_args()

    report = generate_final_report(
        top_k=args.top_k,
        out_html=args.out_html,
        out_pdf=args.out_pdf,
    )
    print("Отчёт:", report["paths"])
    print("Метрики:", json.dumps(report["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
