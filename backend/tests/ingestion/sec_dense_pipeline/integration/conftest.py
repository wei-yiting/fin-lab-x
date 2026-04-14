import os
import pytest
from unittest.mock import patch
import numpy as np

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
TEST_COLLECTION = "test_sec_filings_ci"

@pytest.fixture(autouse=True)
def _set_test_collection(monkeypatch):
    """Force all tests to use isolated test collection."""
    monkeypatch.setenv("SEC_QDRANT_COLLECTION", TEST_COLLECTION)

@pytest.fixture(autouse=True)
def _unset_disable_jit(monkeypatch):
    """Ensure JIT is enabled by default in tests."""
    monkeypatch.delenv("SEC_DISABLE_JIT", raising=False)

@pytest.fixture()
def mock_openai_embed():
    """Mock OpenAI embedding to return deterministic vectors matching _EMBED_DIM."""
    from backend.ingestion.sec_dense_pipeline.vectorizer import _EMBED_DIM
    async def fake_embed(texts):
        return [np.random.default_rng(hash(t) % 2**32).random(_EMBED_DIM).tolist() for t in texts]
    with patch("backend.ingestion.sec_dense_pipeline.vectorizer._embed_texts", new=fake_embed) as m:
        yield m

@pytest.fixture()
def clean_collection():
    """Delete and recreate test collection before each test."""
    from qdrant_client import QdrantClient
    client = QdrantClient(url=QDRANT_URL)
    if client.collection_exists(TEST_COLLECTION):
        client.delete_collection(TEST_COLLECTION)
    yield
    if client.collection_exists(TEST_COLLECTION):
        client.delete_collection(TEST_COLLECTION)

FIXTURE_MARKDOWN_CLASS_A = """
# Item 1. Business

## Product Overview

We design GPUs for data centers and gaming.

## Revenue Breakdown

Revenue grew 122% year-over-year.

# Item 1A. Risk Factors

## Risks Related to Our Industry

Export controls limit access to U.S. licenses for certain customers.

## Risks Related to Our Operations

Supply chain concentration in TSMC creates single-source dependency.

# Item 7. Management's Discussion and Analysis

## Critical Accounting Estimates

### Inventories

Inventory valuation requires significant judgment.
"""

FIXTURE_MARKDOWN_CLASS_C = """
# Item 1. Business

We manufacture semiconductor products for computing and networking.

# Item 1A. Risk Factors

Competition in the semiconductor industry is intense.

# Item 7. Management's Discussion and Analysis

Revenue declined 20% due to market conditions.
"""
