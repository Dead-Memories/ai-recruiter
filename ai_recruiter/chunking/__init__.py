"""Чанкинг текста резюме по смысловым секциям."""

from ai_recruiter.chunking.chunker import (
    FULL_SECTION,
    HEADER_ALIASES,
    PERSONAL_SECTION,
    Chunk,
    chunk_file,
    chunk_resume,
)

__all__ = [
    "FULL_SECTION",
    "HEADER_ALIASES",
    "PERSONAL_SECTION",
    "Chunk",
    "chunk_file",
    "chunk_resume",
]
