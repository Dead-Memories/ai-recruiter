"""Unit-тесты эмбеддингов (fallback-бэкенд без тяжёлых зависимостей)."""

from __future__ import annotations

import math

from ai_recruiter.embeddings import HashingEmbedder, InMemoryVectorStore


class TestHashingEmbedder:
    def test_returns_normalized_vectors(self):
        emb = HashingEmbedder(dim=128)
        vecs = emb.encode(["hello world", "python backend"])
        assert len(vecs) == 2
        for v in vecs:
            assert len(v) == 128
            norm = math.sqrt(sum(x * x for x in v))
            assert abs(norm - 1.0) < 1e-6

    def test_similar_texts_closer_than_dissimilar(self):
        emb = HashingEmbedder(dim=256)
        a = emb.encode(["python docker kubernetes"])[0]
        b = emb.encode(["python docker"])[0]
        c = emb.encode(["java selenium"])[0]
        sim_ab = sum(x * y for x, y in zip(a, b))
        sim_ac = sum(x * y for x, y in zip(a, c))
        assert sim_ab > sim_ac

    def test_deterministic(self):
        emb = HashingEmbedder()
        assert emb.encode(["abc"]) == emb.encode(["abc"])


class TestInMemoryVectorStore:
    def test_query_orders_by_score(self):
        store = InMemoryVectorStore()
        emb = HashingEmbedder()
        store.add("c1", "skills", "python", emb.encode(["python"])[0])
        store.add("c2", "skills", "java", emb.encode(["java"])[0])
        q = emb.encode(["python"], is_query=True)[0]
        results = store.query(q, top_k=2)
        assert results[0].candidate_id == "c1"

    def test_count_and_reset(self):
        store = InMemoryVectorStore()
        emb = HashingEmbedder()
        store.add("c1", "skills", "x", emb.encode(["x"])[0])
        assert store.count() == 1
        store.reset()
        assert store.count() == 0
