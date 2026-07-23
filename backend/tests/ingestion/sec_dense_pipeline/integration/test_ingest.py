from unittest.mock import patch

import numpy as np
import pytest

from backend.ingestion.sec_dense_pipeline.vectorizer import _EMBED_DIM
from backend.tests.ingestion.sec_dense_pipeline.integration.conftest import (
    FIXTURE_MARKDOWN_CLASS_A,
    FIXTURE_MARKDOWN_CLASS_C,
    QDRANT_URL,
    TEST_COLLECTION,
)

pytestmark = pytest.mark.asyncio


def _qdrant_count(ticker: str) -> int:
    """Count content points (non-sentinel) for a ticker."""
    from qdrant_client import QdrantClient, models

    client = QdrantClient(url=QDRANT_URL)
    result = client.count(
        collection_name=TEST_COLLECTION,
        count_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="ticker", match=models.MatchValue(value=ticker)
                ),
            ],
            must_not=[
                models.FieldCondition(
                    key="status",
                    match=models.MatchAny(any=["pending", "complete"]),
                ),
            ],
        ),
    )
    return result.count


@pytest.mark.integration
async def test_class_a_produces_deep_header_path(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing
    from qdrant_client import QdrantClient

    await ingest_filing(ticker="NVDA", year=2025, markdown=FIXTURE_MARKDOWN_CLASS_A)

    client = QdrantClient(url=QDRANT_URL)
    points = client.scroll(collection_name=TEST_COLLECTION, limit=100)[0]

    content_points = [p for p in points if p.payload.get("status") is None]
    header_paths = [p.payload["header_path"] for p in content_points]

    deep_paths = [hp for hp in header_paths if len(hp.split(" / ")) >= 4]
    assert len(deep_paths) > 0, (
        f"No deep header paths found. Paths: {header_paths}"
    )

    items = [p.payload["item"] for p in content_points]
    assert "Item 1A" in items


@pytest.mark.integration
async def test_class_c_produces_shallow_header_path(
    clean_collection, mock_openai_embed
):
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing
    from qdrant_client import QdrantClient

    await ingest_filing(ticker="INTC", year=2025, markdown=FIXTURE_MARKDOWN_CLASS_C)

    client = QdrantClient(url=QDRANT_URL)
    points = client.scroll(collection_name=TEST_COLLECTION, limit=100)[0]
    content_points = [p for p in points if p.payload.get("status") is None]
    header_paths = [p.payload["header_path"] for p in content_points]

    for hp in header_paths:
        levels = len(hp.split(" / "))
        assert levels <= 4, (
            f"Expected shallow paths, got {levels} levels: {hp}"
        )


@pytest.mark.integration
async def test_all_metadata_fields_populated(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing
    from qdrant_client import QdrantClient

    await ingest_filing(ticker="NVDA", year=2025, markdown=FIXTURE_MARKDOWN_CLASS_A)

    client = QdrantClient(url=QDRANT_URL)
    points = client.scroll(collection_name=TEST_COLLECTION, limit=100)[0]
    content_points = [p for p in points if p.payload.get("status") is None]

    assert len(content_points) > 0
    for p in content_points:
        payload = p.payload
        assert payload["ticker"] == "NVDA"
        assert payload["year"] == 2025
        assert payload["filing_type"] == "10-K"
        assert payload["item"] in ("Item 1", "Item 1A", "Item 7", "_unknown")
        assert payload["header_path"].startswith("NVDA / 2025 / ")
        assert (
            isinstance(payload["chunk_index"], int)
            and payload["chunk_index"] >= 0
        )
        assert len(payload["text"]) > 0
        assert (
            isinstance(payload["ingested_at"], str)
            and len(payload["ingested_at"]) > 0
        )


@pytest.mark.integration
async def test_reingest_same_filing_no_duplicates(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing

    await ingest_filing(ticker="NVDA", year=2025, markdown=FIXTURE_MARKDOWN_CLASS_A)
    count_1 = _qdrant_count("NVDA")

    await ingest_filing(ticker="NVDA", year=2025, markdown=FIXTURE_MARKDOWN_CLASS_A)
    count_2 = _qdrant_count("NVDA")

    assert count_1 == count_2
    assert count_1 > 0


@pytest.mark.integration
async def test_partial_failure_sentinel_pending(clean_collection):
    from backend.ingestion.sec_dense_pipeline.common import sentinel_id
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing
    from qdrant_client import QdrantClient

    call_count = 0

    async def fail_after_3(texts):
        nonlocal call_count
        call_count += len(texts)
        if call_count > 3:
            raise Exception("Simulated OpenAI failure")
        return [
            np.random.default_rng(42).random(_EMBED_DIM).tolist() for _ in texts
        ]

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer._embed_texts",
        new=fail_after_3,
    ):
        with pytest.raises(Exception, match="Simulated"):
            await ingest_filing(
                ticker="TEST", year=2025, markdown=FIXTURE_MARKDOWN_CLASS_A
            )

    client = QdrantClient(url=QDRANT_URL)
    points = client.retrieve(
        collection_name=TEST_COLLECTION,
        ids=[sentinel_id("TEST", 2025)],
        with_payload=True,
    )
    assert len(points) == 1
    assert points[0].payload["status"] == "pending"


@pytest.mark.integration
async def test_rerun_after_partial_failure_recovers(clean_collection, mock_openai_embed):
    from backend.ingestion.sec_dense_pipeline.common import sentinel_id
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing
    from qdrant_client import QdrantClient

    call_count = 0

    async def fail_after_3(texts):
        nonlocal call_count
        call_count += len(texts)
        if call_count > 3:
            raise Exception("Simulated OpenAI failure")
        return [
            np.random.default_rng(42).random(_EMBED_DIM).tolist() for _ in texts
        ]

    with patch(
        "backend.ingestion.sec_dense_pipeline.vectorizer._embed_texts",
        new=fail_after_3,
    ):
        try:
            await ingest_filing(
                ticker="TEST", year=2025, markdown=FIXTURE_MARKDOWN_CLASS_A
            )
        except Exception:
            pass

    client = QdrantClient(url=QDRANT_URL)
    points = client.retrieve(
        collection_name=TEST_COLLECTION,
        ids=[sentinel_id("TEST", 2025)],
        with_payload=True,
    )
    assert len(points) == 1
    assert points[0].payload["status"] == "pending"

    await ingest_filing(
        ticker="TEST", year=2025, markdown=FIXTURE_MARKDOWN_CLASS_A
    )

    points = client.retrieve(
        collection_name=TEST_COLLECTION,
        ids=[sentinel_id("TEST", 2025)],
        with_payload=True,
    )
    assert len(points) == 1
    assert points[0].payload["status"] == "complete"

    count = _qdrant_count("TEST")
    assert count > 0


@pytest.mark.integration
def test_batch_cli_retry_and_summary(clean_collection, mock_openai_embed, capsys):
    from unittest.mock import MagicMock

    from backend.ingestion.sec_dense_pipeline.common import sentinel_id
    from backend.common.sec_core import (
        FilingNotFoundError,
        FilingType,
    )
    from backend.scripts.embed_sec_filings import main
    from qdrant_client import QdrantClient

    fixtures = {
        "NVDA": FIXTURE_MARKDOWN_CLASS_A,
        "INTC": FIXTURE_MARKDOWN_CLASS_C,
    }

    def fake_process(ticker, filing_type, fiscal_year=None, force=False, on_retry=None):
        if ticker not in fixtures:
            raise FilingNotFoundError(f"No 10-K filing for ticker={ticker}")
        filing = MagicMock()
        filing.markdown_content = fixtures[ticker]
        filing.metadata = MagicMock()
        filing.metadata.fiscal_year = 2025
        filing.metadata.filing_date = "2025-02-28"
        filing.metadata.filing_type = FilingType.TEN_K
        filing.metadata.accession_number = "0001234567-25-000001"
        return filing

    fake_pipeline = MagicMock()
    fake_pipeline.process.side_effect = fake_process

    with patch(
        "backend.scripts.embed_sec_filings.SECFilingPipeline.create",
        return_value=fake_pipeline,
    ):
        exit_code = main(["NVDA", "FAIL_TICKER", "INTC"])

    captured = capsys.readouterr()
    assert "NVDA" in captured.out
    assert "INTC" in captured.out
    assert "FAIL_TICKER" in captured.out
    assert "success" in captured.out.lower()
    assert "skipped" in captured.out.lower()
    assert exit_code == 1

    client = QdrantClient(url=QDRANT_URL)
    for ticker in ["NVDA", "INTC"]:
        points = client.retrieve(
            collection_name=TEST_COLLECTION,
            ids=[sentinel_id(ticker, 2025)],
            with_payload=True,
        )
        assert len(points) == 1
        assert points[0].payload["status"] == "complete"
