import pytest
from pydantic import ValidationError

from backend.ingestion.sec_text_pipeline.filing_models import (
    FilingMetadata,
    FlatItem,
    ParsedFiling,
    StructuredItem,
)
from backend.tests.ingestion.sec_text_pipeline.conftest import (
    make_metadata,
    make_structured_item,
)


class TestStructuredItemInvariants:
    def test_blocks_must_have_at_least_one(self):
        with pytest.raises(ValidationError):
            make_structured_item(blocks=[])

    def test_kind_defaults_to_structured(self):
        assert make_structured_item().kind == "structured"

    @pytest.mark.parametrize("source", ["markdown_h3", "markdown_h4", "text_fallback"])
    def test_detection_source_accepts_the_three_paths(self, source):
        assert make_structured_item(detection_source=source).detection_source == source

    def test_detection_source_rejects_unknown_path(self):
        with pytest.raises(ValidationError):
            make_structured_item(detection_source="html_heuristic")

    def test_empty_prelude_is_allowed(self):
        assert make_structured_item(prelude="").prelude == ""


class TestFlatItem:
    def test_kind_defaults_to_flat(self):
        flat = FlatItem(item="1b", title="Unresolved Staff Comments", text="None.")
        assert flat.kind == "flat"

    def test_flat_item_has_no_detection_source(self):
        # detection_source records which of the three detection paths found
        # block structure — a FlatItem by definition had none, so the field
        # must not exist on it at all (absent, not merely null).
        assert "detection_source" not in FlatItem.model_fields


class TestParsedFilingRoundTrip:
    def test_discriminated_union_round_trip(self):
        filing = ParsedFiling(
            metadata=make_metadata(),
            items=[
                make_structured_item(),
                FlatItem(item="1b", title="Unresolved Staff Comments", text="None."),
            ],
        )
        restored = ParsedFiling.model_validate_json(filing.model_dump_json())
        assert restored == filing
        assert isinstance(restored.items[0], StructuredItem)
        assert isinstance(restored.items[1], FlatItem)

    def test_union_discriminates_on_kind_not_field_shape(self):
        payload = {
            "metadata": make_metadata().model_dump(mode="json"),
            "items": [
                {
                    "kind": "flat",
                    "item": "2",
                    "title": "Properties",
                    "text": "Our headquarters...",
                }
            ],
        }
        restored = ParsedFiling.model_validate(payload)
        assert isinstance(restored.items[0], FlatItem)

    def test_unknown_kind_rejected(self):
        payload = {
            "metadata": make_metadata().model_dump(mode="json"),
            "items": [{"kind": "markdown", "item": "2", "title": "x", "text": "y"}],
        }
        with pytest.raises(ValidationError):
            ParsedFiling.model_validate(payload)

    def test_unknown_top_level_field_rejected(self):
        # extra="forbid" round-trip guard: a payload field the schema does
        # not know must fail validation, not be silently discarded (silent
        # discard would hide schema drift in stored filings).
        payload = ParsedFiling(
            metadata=make_metadata(), items=[make_structured_item()]
        ).model_dump(mode="json")
        payload["schema_version"] = 2
        with pytest.raises(ValidationError):
            ParsedFiling.model_validate(payload)

    def test_unknown_nested_field_rejected(self):
        payload = ParsedFiling(
            metadata=make_metadata(), items=[make_structured_item()]
        ).model_dump(mode="json")
        payload["items"][0]["confidence"] = 0.9
        with pytest.raises(ValidationError):
            ParsedFiling.model_validate(payload)

    def test_empty_items_list_is_allowed(self):
        # Source-level missing items (e.g. GS 1A/7A) can leave a filing with
        # few or zero parsed items — the schema must not reject that; failure
        # legibility is the parser's job, not the model's.
        filing = ParsedFiling(metadata=make_metadata(), items=[])
        assert filing.items == []


class TestFilingMetadata:
    def test_citation_chain_fields_are_required(self):
        for field in ("accession_number", "cik", "primary_document"):
            payload = make_metadata().model_dump()
            del payload[field]
            with pytest.raises(ValidationError):
                FilingMetadata(**payload)

    def test_filing_type_serializes_as_string(self):
        dumped = make_metadata().model_dump(mode="json")
        assert dumped["filing_type"] == "10-K"
