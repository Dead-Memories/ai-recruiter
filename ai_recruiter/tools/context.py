"""Разделяемый контекст поиска (хранилище + эмбеддер) для тулов.

Агенты вызывают тулы как обычные функции; контекст подставляется лениво:
при первом вызове создаются хранилище и эмбеддер по умолчанию. Пайплайн
может явно установить уже построенный индекс через `set_search_context`.
"""

from __future__ import annotations

from ai_recruiter.embeddings import EmbeddingModel, VectorStore, get_embedder, get_store

_store: VectorStore | None = None
_embedder: EmbeddingModel | None = None


def set_search_context(
    store: VectorStore | None = None,
    embedder: EmbeddingModel | None = None,
) -> None:
    """Устанавливает хранилище/эмбеддер, используемые тулами поиска."""
    global _store, _embedder
    if store is not None:
        _store = store
    if embedder is not None:
        _embedder = embedder


def get_search_context() -> tuple[VectorStore, EmbeddingModel]:
    """Возвращает (store, embedder), создавая их лениво при необходимости."""
    global _store, _embedder
    if _store is None:
        _store = get_store()
    if _embedder is None:
        _embedder = get_embedder()
    return _store, _embedder


__all__ = ["set_search_context", "get_search_context"]
