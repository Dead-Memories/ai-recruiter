"""Эмбеддинги текста с fallback.

Основной путь — sentence-transformers (модель из `config.embedding_model`,
по умолчанию `intfloat/multilingual-e5-large`). Модель e5 требует префиксы
`query:` / `passage:` перед текстом, поэтому они вынесены в конфиг.

Если `sentence-transformers` не установлен (или недоступен на текущем
Python), используется детерминированный хэшинг-эмбеддер на n-граммах
символов: он тоже даёт косинусную близость, зависящую от лексического
пересечения, и позволяет прогнать пайплайн и тесты без тяжёлых зависимостей.
"""

from __future__ import annotations

import hashlib
import importlib.util
import math
from typing import Protocol

from ai_recruiter.config import config

_ST_AVAILABLE = importlib.util.find_spec("sentence_transformers") is not None


class EmbeddingModel(Protocol):
    """Контракт эмбеддера: текст(ы) -> вектор(ы) единичной длины."""

    def encode(self, texts: list[str], *, is_query: bool = False) -> list[list[float]]:
        ...


class HashingEmbedder:
    """Детерминированный fallback-эмбеддер на n-граммах символов.

    Не зависит от внешних библиотек и работает одинаково на любых платформах.
    Даёт приличное качество для лексического пересечения (вакансия/резюме
    на одном языке), чего достаточно для демо и тестов.
    """

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        lowered = text.lower()
        for n in (1, 2, 3):
            for i in range(len(lowered) - n + 1):
                gram = lowered[i : i + n]
                digest = hashlib.md5(gram.encode("utf-8")).digest()
                idx = int.from_bytes(digest[:4], "big") % self.dim
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def encode(self, texts: list[str], *, is_query: bool = False) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]


class SentenceTransformerEmbedder:
    """Обёртка над sentence-transformers с префиксами e5."""

    def __init__(
        self,
        model_name: str | None = None,
        query_prefix: str | None = None,
        passage_prefix: str | None = None,
    ) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name or config.embedding_model)
        self._query_prefix = (
            config.query_prefix if query_prefix is None else query_prefix
        )
        self._passage_prefix = (
            config.passage_prefix if passage_prefix is None else passage_prefix
        )

    def encode(self, texts: list[str], *, is_query: bool = False) -> list[list[float]]:
        prefix = self._query_prefix if is_query else self._passage_prefix
        prefixed = [prefix + t for t in texts]
        vectors = self._model.encode(
            prefixed, normalize_embeddings=True, show_progress_bar=False
        )
        return [v.tolist() for v in vectors]


def get_embedder(model_name: str | None = None) -> EmbeddingModel:
    """Возвращает эмбеддер: sentence-transformers, если доступен, иначе fallback."""
    if _ST_AVAILABLE:
        return SentenceTransformerEmbedder(model_name=model_name)
    return HashingEmbedder()


__all__ = [
    "EmbeddingModel",
    "HashingEmbedder",
    "SentenceTransformerEmbedder",
    "get_embedder",
]
