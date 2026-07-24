from pathlib import Path

import pytest

from backend.tests.ingestion.sec_dense_pipeline.integration.conftest import (
    FIXTURE_MARKDOWN_CLASS_A,
    QDRANT_URL,
    TEST_COLLECTION,
)


@pytest.mark.integration
def test_pre_run_raises_on_missing_collection(clean_collection):
    """Pre-run against a missing Qdrant collection must raise, not score noise.

    Drives the real pre_run hook instead of a local copy so this test can never
    drift from production behaviour (audit G2).
    """
    from backend.evals.eval_tasks import pre_run_sec_retrieval

    with pytest.raises(RuntimeError, match="does not exist"):
        pre_run_sec_retrieval()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pre_run_returns_content_count_excluding_commit_marker(
    clean_collection, mock_openai_embed
):
    """Pre-run reports the collection and its content-point count.

    The count must exclude the bookkeeping commit marker that ingestion
    writes — the exact behaviour the old drifted copy got wrong by counting
    every point.
    """
    from qdrant_client import QdrantClient

    from backend.evals.eval_tasks import pre_run_sec_retrieval
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing

    await ingest_filing(ticker="NVDA", year=2025, markdown=FIXTURE_MARKDOWN_CLASS_A)

    result = pre_run_sec_retrieval()

    client = QdrantClient(url=QDRANT_URL)
    total_points = client.count(collection_name=TEST_COLLECTION).count

    assert result["Collection"] == TEST_COLLECTION
    assert result["Points"] >= 1
    # Exactly one commit marker (status=complete) is excluded from the content count.
    assert result["Points"] == total_points - 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pre_run_raises_when_only_commit_marker_present(clean_collection):
    """Collection exists but holds only a commit marker → 0 content points → raise.

    Guards the exclusion logic's guard branch: a collection with no real chunk
    content (only bookkeeping commit-marker points) must fail fast rather than
    score against an empty index.
    """
    from qdrant_client import AsyncQdrantClient, models

    from backend.evals.eval_tasks import pre_run_sec_retrieval
    from backend.ingestion.sec_dense_pipeline.collection_schema import (
        async_ensure_collection_and_indexes,
    )
    from backend.ingestion.sec_dense_pipeline.common import commit_marker_id
    from backend.ingestion.sec_dense_pipeline.vectorizer import _EMBED_DIM

    client = AsyncQdrantClient(url=QDRANT_URL)
    try:
        await async_ensure_collection_and_indexes(
            client, TEST_COLLECTION, vector_size=_EMBED_DIM
        )
        await client.upsert(
            collection_name=TEST_COLLECTION,
            points=[
                models.PointStruct(
                    id=commit_marker_id("NVDA", 2025),
                    vector=[0.0] * _EMBED_DIM,
                    payload={"ticker": "NVDA", "year": 2025, "status": "complete"},
                )
            ],
        )
    finally:
        await client.close()

    with pytest.raises(RuntimeError, match="0 content points"):
        pre_run_sec_retrieval()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_validator_catches_case_mismatch(
    clean_collection, mock_openai_embed, tmp_path
):
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing
    from backend.scripts.validation.validate_sec_eval_dataset import validate_dataset

    await ingest_filing(ticker="NVDA", year=2025, markdown=FIXTURE_MARKDOWN_CLASS_A)

    # Write test CSV with deliberate case error ("item 1a" vs actual "Item 1A")
    csv_path = tmp_path / "test_dataset.csv"
    csv_path.write_text(
        "question,expected_header_paths,expected_tickers,match_mode\n"
        '"test","[""NVDA / 2025 / item 1a""]","[""NVDA""]","startswith"\n'
    )

    exit_code = validate_dataset(
        csv_path=Path(csv_path),
        qdrant_url=QDRANT_URL,
        collection=TEST_COLLECTION,
    )
    assert exit_code == 1  # non-zero due to case mismatch
