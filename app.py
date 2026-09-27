"""Streamlit-демо: подбор кандидатов под вакансию.

Запуск:
    pip install streamlit
    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from ai_recruiter.embeddings import build_index, load_manifest
from ai_recruiter.pipeline import run_pipeline
from ai_recruiter.report.final_report import load_all_vacancies
from ai_recruiter.schema import Vacancy


@st.cache_resource
def _build_index():
    manifest = load_manifest()
    return build_index(manifest=manifest), manifest


@st.cache_data
def _vacancies() -> list[dict]:
    return [{"title": v.title, "role": v.role} for v in load_all_vacancies()]


def main() -> None:
    st.set_page_config(page_title="AI-Recruiter", layout="wide")
    st.title("AI-Recruiter")
    st.caption("Мультиагентная система семантического ранжирования и скоринга кандидатов")

    vacancies = load_all_vacancies()
    titles = [v.title for v in vacancies]
    choice = st.selectbox("Вакансия", titles, index=0)
    vacancy = vacancies[titles.index(choice)]

    top_k = st.slider("Количество кандидатов", min_value=1, max_value=20, value=5)

    if st.button("Подобрать кандидатов", type="primary"):
        with st.spinner("Строим индекс и ранжируем..."):
            store, manifest = _build_index()
            reports = run_pipeline(
                vacancy, top_k=top_k, store=store, manifest=manifest
            )

        if not reports:
            st.warning("Кандидаты не найдены.")
            return

        st.subheader(f"Топ-{len(reports)} кандидатов: {vacancy.title}")
        for i, report in enumerate(reports, start=1):
            verdict_color = {
                "Рекомендован": "green",
                "В резерв": "orange",
                "Отказ": "red",
            }.get(report.verdict, "gray")
            with st.container(border=True):
                cols = st.columns([3, 1, 1])
                cols[0].markdown(f"**{i}. {report.full_name}** — {report.role}")
                cols[1].metric("Соответствие", f"{report.score}%")
                cols[2].markdown(
                    f":{verdict_color}[{report.verdict}]"
                )
                st.markdown(
                    f"*Опыт:* {report.years_experience:.1f} лет | "
                    f"*Тех:* {report.technical_score} | *HR:* {report.hr_score} | "
                    f"*Семантика:* {report.semantic_score}"
                )
                c1, c2, c3 = st.columns(3)
                c1.markdown("**Плюсы**\n" + "\n".join(f"- {p}" for p in report.pros or ["—"]))
                c2.markdown("**Минусы**\n" + "\n".join(f"- {c}" for c in report.cons or ["—"]))
                c3.markdown("**Риски**\n" + "\n".join(f"- {r}" for r in report.risks or ["—"]))


if __name__ == "__main__":
    main()
