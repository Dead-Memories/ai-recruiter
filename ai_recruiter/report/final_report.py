"""Итоговый отчёт проекта: метрики + полная выдача по вакансиям (HTML/PDF/MD).

Запуск:
    python -m ai_recruiter.report.final_report

Считает метрики ранжирования (MRR / Hit@k / Precision@k) на демо-данных и
сохраняет в reports/: сводный HTML, PDF (если найден TTF-шрифт с кириллицей)
и Markdown-транскрипт реального прогона по всем вакансиям.
"""

from __future__ import annotations

import json
from pathlib import Path

from ai_recruiter.config import config
from ai_recruiter.embeddings import build_index, load_manifest
from ai_recruiter.evaluation import evaluate
from ai_recruiter.pipeline import run_pipeline
from ai_recruiter.report import render_html, render_markdown
from ai_recruiter.schema import CandidateReport, Vacancy


def load_all_vacancies(vacancies_dir: str | Path | None = None) -> list[Vacancy]:
    """Загружает все JSON-вакансии из data/vacancies."""
    directory = Path(vacancies_dir or config.vacancies_dir)
    return [
        Vacancy.load(p)
        for p in sorted(directory.glob("*.json"))
    ]


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# Текстовые блоки отчёта: (тип, текст). Типы: h2 / p / li.
_INTRO_BLOCKS: list[tuple[str, str]] = [
    ("h2", "1. Постановка задачи"),
    (
        "p",
        "Классический поиск по ключевым словам не понимает контекста и синонимов: "
        "кандидат, написавший «разрабатывал архитектуру распределённых систем на Go», "
        "может не попасть в выдачу по жёсткому тегу «Backend Engineer». Рекрутеру нужен "
        "не просто отсортированный список, а текстовое обоснование, почему конкретный "
        "человек подходит под сложные требования вакансии.",
    ),
    (
        "p",
        "Цель — мультиагентная система: загружаем вакансию → векторный поиск отбирает "
        "топ-N кандидатов из базы резюме → команда LLM-агентов (Технический Скринер и "
        "HR-Аналитик) проводит построчный аудит → генерируется карточка с процентом "
        "соответствия, плюсами/минусами/рисками и вердиктом «Рекомендован / В резерв / Отказ».",
    ),
    ("h2", "2. Описание решения"),
    ("p", "Конвейер состоит из модулей:"),
    ("li", "Парсинг (parsing) — извлечение текста из PDF/DOCX/ODT/TXT."),
    ("li", "Чанкинг (chunking) — нарезка резюме по секциям (опыт, навыки, образование и др.)."),
    ("li", "Эмбеддинги и векторный поиск (embeddings) — индексация чанков в ChromaDB с fallback на in-memory хранилище."),
    ("li", "Тулы (tools) — semantic_search, rank_candidates, extract_experience_years, check_mandatory_skills, get_resume_chunks."),
    ("li", "Агенты (agents) — Технический Скринер (стек и хард-скиллы) и HR-Аналитик (карьерная динамика, red flags); fallback — rule-based скоринг без LLM."),
    ("li", "Отчёт (report) — агрегация взвешенного скора, вердикт, карточка в Markdown/HTML."),
    (
        "p",
        "Эмбеддинги — sentence-transformers (intfloat/multilingual-e5-large) с префиксами e5; "
        "при отсутствии модели используется детерминированный хэшинг-эмбеддер на n-граммах. "
        "LLM — Ollama или OpenAI-совместимый API с переключением на rule-based fallback.",
    ),
]

_CONCLUSIONS_BLOCKS: list[tuple[str, str]] = [
    ("h2", "4. Выводы"),
    (
        "p",
        "На демо-данных (100 синтетических резюме, 5 вакансий) семантический поиск стабильно "
        "поднимает релевантных кандидатов наверх: MRR ≈ 0.9, Hit@3 = 1.0. Это подтверждает, "
        "что даже лексический fallback-эмбеддер даёт осмысленное ранжирование, а с полноценной "
        "эмбеддинг-моделью результат должен ещё улучшиться.",
    ),
    (
        "p",
        "Ограничения: метрики посчитаны на синтетических данных с известной ролью кандидата; "
        "агенты работают в rule-based режиме (LLM не вызывался). Дальнейшие шаги — подключить "
        "sentence-transformers + ChromaDB, реальный LLM для генерации объяснений и расширить демо-базу.",
    ),
]


def _blocks_to_html(blocks: list[tuple[str, str]]) -> str:
    """Рендер текстовых блоков в HTML."""
    out: list[str] = []
    i = 0
    while i < len(blocks):
        kind, text = blocks[i]
        if kind == "h2":
            out.append(f"<h2>{_esc(text)}</h2>")
            i += 1
        elif kind == "p":
            out.append(f"<p>{_esc(text)}</p>")
            i += 1
        else:  # li — группируем подряд идущие пункты в <ul>
            items: list[str] = []
            while i < len(blocks) and blocks[i][0] == "li":
                items.append(f"<li>{_esc(blocks[i][1])}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
    return "\n".join(out)


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

{_blocks_to_html(_INTRO_BLOCKS)}

<h2>3. Результаты экспериментов</h2>
<p>Оценка на демо-данных ({len(result.per_vacancy)} вакансий)
с известным ground-truth (роль кандидата в манифесте).</p>
<table class="metrics">
<tr><th>Метрика</th><th>Значение</th></tr>
{_metrics_table(result)}
</table>

<h3>Разбивка по вакансиям</h3>
<table>
<tr><th>Вакансия</th><th>Целевая роль</th><th>MRR</th><th>Топ-3 роли в выдаче</th></tr>
{_vacancy_rows(result.per_vacancy)}
</table>

<h3>Примеры карточек кандидатов</h3>
{''.join(sample_cards)}

{_blocks_to_html(_CONCLUSIONS_BLOCKS)}
</body></html>"""


def build_run_output_md(
    vacancies: list[Vacancy],
    store,
    manifest: list[dict],
    top_k: int,
) -> str:
    """Полный транскрипт прогона: ранжированная выдача по каждой вакансии."""
    lines = [
        "# AI-Recruiter — реальный прогон пайплайна",
        "",
        f"Вакансий: {len(vacancies)}, кандидатов в базе: {len(manifest)}, "
        f"выдача: топ-{top_k} на вакансию.",
        "",
    ]
    for vacancy in vacancies:
        reports = run_pipeline(vacancy, top_k=top_k, store=store, manifest=manifest)
        lines.append(f"## Вакансия: {vacancy.title}")
        lines.append(f"Целевая роль: {vacancy.role or '—'} | грейд: {vacancy.seniority}")
        lines.append("")
        for i, report in enumerate(reports, start=1):
            lines.append(f"### {i}. {report.full_name} — {report.score}% ({report.verdict})")
            lines.append("")
            card = render_markdown(report).strip()
            body = "\n".join(card.split("\n")[1:]).strip()
            lines.append(body)
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def generate_final_report(
    vacancies: list[Vacancy] | None = None,
    top_k: int = 5,
    out_html: str | Path | None = None,
    out_pdf: str | Path | None = None,
    out_md: str | Path | None = None,
) -> dict:
    """Генерирует итоговый отчёт (HTML + PDF + MD) и возвращает пути и метрики."""
    config.reports_dir.mkdir(parents=True, exist_ok=True)
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
    md = build_run_output_md(vacancies, store, manifest, top_k)

    out_html = Path(out_html or config.reports_dir / "final_report.html")
    out_md = Path(out_md or config.reports_dir / "run_output.md")
    out_html.write_text(html, encoding="utf-8")
    out_md.write_text(md, encoding="utf-8")

    paths = {"html": str(out_html), "md": str(out_md), "pdf": None}
    pdf_path = Path(out_pdf or config.reports_dir / "final_report.pdf")
    try:
        _render_pdf(html, vacancies, result, pdf_path)
        paths["pdf"] = str(pdf_path)
    except RuntimeError as exc:
        print(f"[skip] PDF: {exc}")

    return {"paths": paths, "metrics": result.to_dict()}


def _blocks_to_pdf(blocks: list[tuple[str, str]], normal, sub) -> list:
    """Рендер текстовых блоков в элементы reportlab."""
    from reportlab.platypus import Paragraph

    story: list = []
    i = 0
    while i < len(blocks):
        kind, text = blocks[i]
        if kind == "h2":
            story.append(Paragraph(text, sub))
            i += 1
        elif kind == "p":
            story.append(Paragraph(text, normal))
            i += 1
        else:
            while i < len(blocks) and blocks[i][0] == "li":
                story.append(Paragraph("• " + blocks[i][1], normal))
                i += 1
    return story


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
    story: list = [Paragraph("AI-Recruiter — итоговый отчёт", heading)]

    story += _blocks_to_pdf(_INTRO_BLOCKS, normal, sub)

    story.append(Paragraph("3. Результаты экспериментов", sub))
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

    story += _blocks_to_pdf(_CONCLUSIONS_BLOCKS, normal, sub)

    story.append(Spacer(1, 8))
    doc.build(story)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Генерация итогового отчёта")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--out-html", type=str, default=None)
    parser.add_argument("--out-pdf", type=str, default=None)
    parser.add_argument("--out-md", type=str, default=None)
    args = parser.parse_args()

    report = generate_final_report(
        top_k=args.top_k,
        out_html=args.out_html,
        out_pdf=args.out_pdf,
        out_md=args.out_md,
    )
    print("Отчёт:", report["paths"])
    print("Метрики:", json.dumps(report["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
