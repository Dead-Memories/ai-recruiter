"""Индексация резюме в векторное хранилище.

Конвейер: файл резюме (PDF/DOCX/…) → извлечение текста → чанкинг по секциям
→ эмбеддинг каждого чанка → запись в векторное хранилище с метаданными
(candidate_id, section).
"""

from __future__ import annotations

import json
from pathlib import Path

from ai_recruiter.chunking import chunk_file
from ai_recruiter.config import config
from ai_recruiter.embeddings.embeddings import EmbeddingModel, get_embedder
from ai_recruiter.embeddings.vector_store import VectorStore, get_store
from ai_recruiter.parsing import ParsingError, extract_text


def load_manifest(manifest_path: str | Path | None = None) -> list[dict]:
    """Загружает манифест кандидатов (ground-truth данные генератора)."""
    path = Path(manifest_path or config.manifest_path)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def index_candidate(
    candidate_id: str,
    resume_path: str | Path,
    store: VectorStore,
    embedder: EmbeddingModel,
) -> int:
    """Индексирует одно резюме. Возвращает число добавленных чанков."""
    text = extract_text(resume_path)
    chunks = chunk_file(resume_path)
    if not chunks:
        return 0

    vectors = embedder.encode([c.text for c in chunks])
    for chunk, vec in zip(chunks, vectors):
        store.add(candidate_id, chunk.section, chunk.text, vec)
    return len(chunks)


def build_index(
    store: VectorStore | None = None,
    embedder: EmbeddingModel | None = None,
    manifest: list[dict] | None = None,
    limit: int | None = None,
) -> VectorStore:
    """Строит индекс по манифесту: парсинг + чанкинг + эмбеддинг + запись.

    Возвращает использованное хранилище (новое, если не передано).
    """
    store = store or get_store()
    embedder = embedder or get_embedder()
    manifest = manifest if manifest is not None else load_manifest()

    entries = manifest[:limit] if limit else manifest
    for entry in entries:
        candidate_id = entry.get("candidate_id", "")
        resume_file = entry.get("resume_file", "")
        if not resume_file:
            continue
        resume_path = config.resumes_dir / resume_file
        if not resume_path.exists():
            continue
        try:
            index_candidate(candidate_id, resume_path, store, embedder)
        except ParsingError:
            continue

    return store


__all__ = [
    "load_manifest",
    "index_candidate",
    "build_index",
]
