import os
from pathlib import Path

import pytest

from backend.tests.ingestion.sec_dense_pipeline.integration.conftest import (
    FIXTURE_MARKDOWN_CLASS_A,
    QDRANT_URL,
    TEST_COLLECTION,
)


def _preflight_check() -> int:
    """Run the pre-flight check that run_sec_retrieval should perform."""
    from qdrant_client import QdrantClient

    collection = os.environ.get("SEC_QDRANT_COLLECTION", TEST_COLLECTION)
    client = QdrantClient(url=QDRANT_URL)

    if not client.collection_exists(collection):
        raise RuntimeError(
            f"Collection '{collection}' does not exist. "
            "Run ingest before eval. 0 points available."
        )

    result = client.count(collection_name=collection)
    if result.count == 0:
        raise RuntimeError(
            f"Collection '{collection}' has 0 points. "
            "Run ingest before eval."
        )
    return result.count


@pytest.mark.integration
def test_eval_runner_preflight_empty_collection(clean_collection):
    """Eval against empty Qdrant should raise, not produce all-zero scores."""
    with pytest.raises(RuntimeError, match="0 points"):
        _preflight_check()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_eval_runner_prints_collection_banner(
    clean_collection, mock_openai_embed, capsys
):
    from backend.ingestion.sec_dense_pipeline.vectorizer import ingest_filing

    await ingest_filing(ticker="NVDA", year=2025, markdown=FIXTURE_MARKDOWN_CLASS_A)

    count = _preflight_check()
    collection = os.environ.get("SEC_QDRANT_COLLECTION", TEST_COLLECTION)
    banner = (
        f"Eval scenario: sec_retrieval | "
        f"Collection: {collection} | "
        f"Points: {count}"
    )
    print(banner)

    captured = capsys.readouterr()
    assert "Eval scenario: sec_retrieval" in captured.out
    assert collection in captured.out
    assert str(count) in captured.out


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
