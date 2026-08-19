"""Центральная конфигурация проекта.

Все пути, seed и параметры моделей собраны здесь, чтобы проверяющий мог
воспроизвести пайплайн без правок кода.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    # --- Пути ---
    data_dir: Path = field(
        default_factory=lambda: PROJECT_ROOT / "data"
    )
    resumes_dir: Path = field(
        default_factory=lambda: PROJECT_ROOT / "data" / "resumes"
    )
    vacancies_dir: Path = field(
        default_factory=lambda: PROJECT_ROOT / "data" / "vacancies"
    )
    manifest_path: Path = field(
        default_factory=lambda: PROJECT_ROOT / "data" / "candidates_manifest.json"
    )
    chroma_dir: Path = field(
        default_factory=lambda: PROJECT_ROOT / "chroma"
    )

    # --- Воспроизводимость ---
    seed: int = 42
    n_resumes: int = 100

    # --- Эмбеддинги ---
    embedding_model: str = "intfloat/multilingual-e5-large"
    # префиксы e5 для корректного эмбеддинга query/passage
    query_prefix: str = "query: "
    passage_prefix: str = "passage: "

    # --- Векторный поиск ---
    top_k: int = 20

    # --- LLM ---
    # "ollama" или "openai" (OpenAI-совместимый API)
    llm_provider: str = "ollama"
    ollama_model: str = "qwen2.5:14b"
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    openai_model: str = "gpt-4o-mini"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.resumes_dir, self.vacancies_dir):
            d.mkdir(parents=True, exist_ok=True)


config = Config()
