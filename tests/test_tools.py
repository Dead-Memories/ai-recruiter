"""Unit-тесты библиотеки тулов."""

from __future__ import annotations

from ai_recruiter.tools import (
    check_mandatory_skills,
    extract_experience_years,
    get_resume_chunks,
    rank_candidates,
    semantic_search,
)


class TestExtractExperienceYears:
    def test_explicit_header(self):
        assert extract_experience_years("Опыт работы — 13 лет 1 месяц") == 13.1

    def test_explicit_years_only(self):
        assert extract_experience_years("Опыт: 5 лет") == 5.0

    def test_month_year_ranges(self):
        text = "08.2020 — наст. время"
        assert extract_experience_years(text) == 5.0

    def test_bare_year_ranges(self):
        text = "2020—2023\n2018—2020"
        assert extract_experience_years(text) == 5.0

    def test_no_dates(self):
        assert extract_experience_years("Просто текст без дат") == 0.0

    def test_empty(self):
        assert extract_experience_years("") == 0.0


class TestCheckMandatorySkills:
    def test_found_and_missing(self):
        res = check_mandatory_skills(
            "Python, FastAPI, Go для backend",
            ["Python", "Go", "Java", "Kubernetes"],
        )
        assert res["found"] == ["Python", "Go"]
        assert res["missing"] == ["Java", "Kubernetes"]
        assert res["ratio"] == 0.5

    def test_case_insensitive(self):
        res = check_mandatory_skills("PYTHON and docker", ["Python", "Docker"])
        assert res["matched"] == 2

    def test_short_skill_word_boundary(self):
        assert check_mandatory_skills("Django backend", ["Go"])["matched"] == 0
        assert check_mandatory_skills("Go backend", ["Go"])["matched"] == 1

    def test_empty_skills(self):
        res = check_mandatory_skills("anything", [])
        assert res["total"] == 0
        assert res["ratio"] == 1.0


class TestSemanticSearch:
    def test_ranks_relevant_candidate_first(self):
        from ai_recruiter.embeddings import HashingEmbedder, InMemoryVectorStore
        from ai_recruiter.tools.context import set_search_context

        store = InMemoryVectorStore()
        embedder = HashingEmbedder()
        store.add("c1", "skills", "Python Django PostgreSQL Docker", embedder.encode(["Python Django PostgreSQL Docker"])[0])
        store.add("c2", "skills", "Java Selenium JUnit", embedder.encode(["Java Selenium JUnit"])[0])

        matches = rank_candidates("Python FastAPI backend", top_k=2, store=store, embedder=embedder)
        assert matches[0].candidate_id == "c1"

    def test_semantic_search_returns_chunks(self):
        from ai_recruiter.embeddings import HashingEmbedder, InMemoryVectorStore

        store = InMemoryVectorStore()
        embedder = HashingEmbedder()
        store.add("c1", "skills", "Python Docker", embedder.encode(["Python Docker"])[0])
        chunks = semantic_search("Python", top_k=1, store=store, embedder=embedder)
        assert chunks[0].candidate_id == "c1"

    def test_get_resume_chunks(self):
        from ai_recruiter.embeddings import HashingEmbedder, InMemoryVectorStore

        store = InMemoryVectorStore()
        embedder = HashingEmbedder()
        store.add("c1", "skills", "Python", embedder.encode(["Python"])[0])
        store.add("c1", "experience", "Яндекс", embedder.encode(["Яндекс"])[0])
        chunks = get_resume_chunks("c1", store=store)
        assert {c.section for c in chunks} == {"skills", "experience"}

    def test_empty_query(self):
        from ai_recruiter.embeddings import HashingEmbedder, InMemoryVectorStore

        store = InMemoryVectorStore()
        embedder = HashingEmbedder()
        assert semantic_search("  ", store=store, embedder=embedder) == []
