"""Эмбеддинги и векторный поиск: индексация чанков резюме в ChromaDB."""

from ai_recruiter.embeddings.embeddings import (
    EmbeddingModel,
    HashingEmbedder,
    SentenceTransformerEmbedder,
    get_embedder,
)
from ai_recruiter.embeddings.indexer import (
    build_index,
    index_candidate,
    load_manifest,
)
from ai_recruiter.embeddings.vector_store import (
    ChromaVectorStore,
    InMemoryVectorStore,
    SearchResult,
    VectorStore,
    get_store,
)

__all__ = [
    "EmbeddingModel",
    "HashingEmbedder",
    "SentenceTransformerEmbedder",
    "get_embedder",
    "build_index",
    "index_candidate",
    "load_manifest",
    "SearchResult",
    "VectorStore",
    "InMemoryVectorStore",
    "ChromaVectorStore",
    "get_store",
]
