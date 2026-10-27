"""Unit tests for the parsing A/B arm adapters (no Qdrant, no OpenAI)."""

import json
from pathlib import Path

import pytest

from backend.common.sec_core import FilingType
from backend.evals.experiments.parsing_ab.arms import (
    TOP_K,
    QueryEmbeddingCache,
    drop_excluded_items,
    html_filters,
    text_filters,
)
from backend.ingestion.sec_text_pipeline.filing_models import (
    Block,
    FilingMetadata,
    FlatItem,
    ParsedFiling,
    StructuredItem,
)


def _filing() -> ParsedFiling:
    return ParsedFiling(
        metadata=FilingMetadata(
            ticker="NVDA",
            cik="0001045810",
            company_name="NVIDIA CORP",
            filing_type=FilingType.TEN_K,
            filing_date="2026-02-25",
            fiscal_year=2026,
            accession_number="0001045810-26-000021",
            primary_document="nvda-20260125.htm",
            parsed_at="2026-08-20T00:00:00+00:00",
        ),
        items=[
            FlatItem(item="1A", title="Risk Factors", text="risk text"),
            StructuredItem(
                item="7",
                title="Management's Discussion",
                prelude="",
                blocks=[Block(heading="Overview", text="mdna text")],
                detection_source="markdown_h3",
            ),
            FlatItem(item=" 8 ", title="Financial Statements", text="notes text"),
        ],
    )


class TestDropExcludedItems:
    def test_removes_item_8_only(self) -> None:
        filtered, dropped = drop_excluded_items(_filing())
        assert [i.item for i in filtered.items] == ["1A", "7"]
        assert dropped == ["8"]

    def test_original_filing_is_untouched(self) -> None:
        filing = _filing()
        drop_excluded_items(filing)
        assert len(filing.items) == 3

    def test_metadata_carried_over(self) -> None:
        filtered, _ = drop_excluded_items(_filing())
        assert filtered.metadata.accession_number == "0001045810-26-000021"


class TestFilters:
    def test_html_arm_excludes_item_8_at_query_time(self) -> None:
        assert html_filters("nvda", 2026) == {
            "ticker": "NVDA",
            "year": 2026,
            "exclude_items": ["Item 8"],
        }

    def test_text_arm_scopes_by_ticker_and_fiscal_year(self) -> None:
        assert text_filters("nvda", 2026) == {"ticker": "NVDA", "fiscal_year": 2026}

    def test_top_k_is_ten(self) -> None:
        assert TOP_K == 10


class TestQueryEmbeddingCache:
    @pytest.mark.asyncio
    async def test_embeds_each_text_once_and_persists(self, tmp_path: Path) -> None:
        calls: list[list[str]] = []

        async def fake_embed(texts: list[str]) -> list[list[float]]:
            calls.append(texts)
            return [[float(len(t))] for t in texts]

        path = tmp_path / "query_embeddings.json"
        cache = QueryEmbeddingCache(path, fake_embed)
        assert await cache(["abc"]) == [[3.0]]
        assert await cache(["abc"]) == [[3.0]]
        assert calls == [["abc"]]
        assert json.loads(path.read_text()) == {"abc": [3.0]}

    @pytest.mark.asyncio
    async def test_reloads_from_disk_without_embedding(self, tmp_path: Path) -> None:
        path = tmp_path / "query_embeddings.json"
        path.write_text(json.dumps({"q": [0.5, 0.25]}))

        async def must_not_embed(texts: list[str]) -> list[list[float]]:
            raise AssertionError("cache miss")

        cache = QueryEmbeddingCache(path, must_not_embed)
        assert await cache(["q"]) == [[0.5, 0.25]]
