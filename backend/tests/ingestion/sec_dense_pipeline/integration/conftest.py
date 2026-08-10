"""Integration fixtures: real local Qdrant, mocked OpenAI embeddings."""

import os
from unittest.mock import patch

import numpy as np
import pytest

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
TEST_COLLECTION = "test_sec_text_dense_ci"


@pytest.fixture(autouse=True)
def _set_test_collection(monkeypatch):
    """Isolate every test in its own new-contract collection."""
    monkeypatch.setenv("SEC_TEXT_QDRANT_COLLECTION", TEST_COLLECTION)


@pytest.fixture()
def mock_openai_embed():
    """Deterministic embeddings matching _EMBED_DIM; no OpenAI calls."""
    from backend.ingestion.sec_dense_pipeline.vectorizer import _EMBED_DIM

    async def fake_embed(texts):
        return [
            np.random.default_rng(hash(t) % 2**32).random(_EMBED_DIM).tolist()
            for t in texts
        ]

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer._embed_texts",
        new=fake_embed,
    ) as m:
        yield m


@pytest.fixture()
def clean_collection():
    """Delete the test collection before and after each test."""
    from qdrant_client import QdrantClient

    client = QdrantClient(url=QDRANT_URL)
    if client.collection_exists(TEST_COLLECTION):
        client.delete_collection(TEST_COLLECTION)
    yield
    if client.collection_exists(TEST_COLLECTION):
        client.delete_collection(TEST_COLLECTION)
