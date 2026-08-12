import re

import pytest

from backend.common.sec_core import (
    FetchedFiling,
    FilingNotFoundError,
    FilingType,
    SECError,
    UnsupportedFilingTypeError,
)
from backend.ingestion.sec_text_pipeline import parser
from backend.ingestion.sec_text_pipeline.filing_models import (
    FlatItem,
    ParsedFiling,
    StructuredItem,
)
from backend.tests.ingestion.sec_text_pipeline.conftest import (
    FakeTenK,
    make_bundle,
    make_metadata,
)


def _full_text(item) -> str:
    """An item's complete body regardless of kind, in document order."""
    if isinstance(item, FlatItem):
        return item.text
    parts = [item.prelude]
    for block in item.blocks:
        parts.extend([block.heading, block.text])
    return "\n".join(p for p in parts if p)


@pytest.fixture
def fetch_calls(monkeypatch, fake_bundle):
    """Patch the EDGAR fetch seam; record every call's arguments."""
    calls: list[tuple[str, FilingType, int | None]] = []

    def fake_fetch(
        ticker: str, filing_type: FilingType, fiscal_year: int | None = None
    ) -> FetchedFiling:
        calls.append((ticker, filing_type, fiscal_year))
        return fake_bundle

    monkeypatch.setattr(parser, "fetch_filing_bundle", fake_fetch)
    return calls


class TestParsedStructure:
    def test_items_structure_via_fallback_without_markdown(self, store, fetch_calls):
        # The markdown seam defaults to empty here, so any structure must
        # come from the text fallback; items it rejects stay flat.
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert isinstance(result, ParsedFiling)
        assert result.items  # non-empty
        structured = [i for i in result.items if isinstance(i, StructuredItem)]
        assert structured  # recorded AAPL reality: fallback finds structure
        assert all(i.detection_source == "text_fallback" for i in structured)
        assert all(isinstance(i, FlatItem | StructuredItem) for i in result.items)

    def test_stub_items_are_dropped(self, store, fetch_calls):
        # Recorded AAPL FY2025 reality: 6 is [Reserved]; 10/11/12/13 are
        # incorporated-by-reference stubs. Item 11's raw section text bleeds
        # Items 12-15 onto its pure pointer stub — only after trimming to
        # its own boundary does it classify (and drop) correctly.
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        emitted = {item.item for item in result.items}
        assert {"6", "10", "11", "12", "13"}.isdisjoint(emitted)
        assert {"1", "1a", "7"} <= emitted

    def test_emitted_text_contains_no_foreign_item_heading(self, store, fetch_calls):
        # Section bleed guard: edgartools returns Item 9C with "PART IIIItem
        # 10." (and onward) glued on, and Item 11 with Items 12-15 glued on.
        # After trimming, no emitted item's text may contain another item's
        # STRUCTURAL heading (line-start or glued). Inline cross-references
        # ("...under Item 1A. Risk Factors...") are legitimate prose and are
        # deliberately not counted.
        heading_re = re.compile(r"Item\s+(\d{1,2}[a-cA-C]?)\s*\.(?!\d)")
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        for item in result.items:
            body = _full_text(item)
            foreign = {
                m.group(1).lower()
                for m in heading_re.finditer(body)
                if m.group(1).lower() != item.item
                and parser._is_structural_boundary(body, m.start())
            }
            assert not foreign, f"item {item.item} text bleeds into {foreign}"
        nine_c = next(item for item in result.items if item.item == "9c")
        assert "Item 10." not in _full_text(nine_c)


class TestTrimSectionText:
    def test_inline_cross_reference_is_preserved(self):
        text = (
            "Item 1C. Cybersecurity\n"
            "We discuss cyber risk under Item 1A. Risk Factors, and then "
            "continue with our risk management program in detail here.\n"
            "More program details follow."
        )
        assert parser._trim_section_text(text, "1c") == text.rstrip()

    def test_newline_anchored_foreign_heading_is_cut(self):
        text = (
            "Item 11. Executive Compensation\n"
            "The information required by this Item is described above.\n"
            "Item 12. Security Ownership\n"
            "Foreign body that must be dropped.\n"
        )
        trimmed = parser._trim_section_text(text, "11")
        assert "Item 11." in trimmed
        assert "Item 12." not in trimmed
        assert "Foreign body" not in trimmed

    def test_glued_foreign_heading_is_cut(self):
        text = (
            "Item 9C. Disclosure Regarding Foreign Jurisdictions\n"
            "None.PART IIIItem 10. Directors, Executive Officers\n"
            "Bled next-part body.\n"
        )
        trimmed = parser._trim_section_text(text, "9c")
        assert "Item 10." not in trimmed
        assert "Bled next-part body" not in trimmed
        # The dangling glued "PART III" label is stripped from the tail too.
        assert not trimmed.endswith("PART III")

    def test_item_inside_larger_word_is_preserved(self):
        # "Item" embedded in a larger word ("SubItem 1.", "LineItem 1A.")
        # is prose, not a heading — a preceding letter is a structural glue
        # only when it closes a "PART <roman>" label.
        text = (
            "Item 7. MD&A discussion. Our ledger tracks each SubItem 1. "
            "remains of the fiscal analysis, and every LineItem 1A. entry "
            "continues here with substantive discussion of results."
        )
        assert parser._trim_section_text(text, "7") == text.rstrip()

    def test_quoted_cross_reference_is_preserved(self):
        # WMT FY2025 Item 1A regression: a quoted cross-reference
        # ('See "Item 1. Business" above') has a quote, not a space, before
        # "Item" — it must read as prose, not as a glued structural
        # boundary (which silently amputated 82k of 93k chars).
        text = (
            "Item 1A. Risk Factors\n"
            'Competition could hurt us. See "Item 1. Business" above for '
            "additional discussion of the competitive landscape.\n"
            "Further substantive risk discussion continues here.\n"
        )
        assert parser._trim_section_text(text, "1a") == text.rstrip()

    def test_all_caps_foreign_heading_is_cut(self):
        # Some filings render section headings in ALL-CAPS ("ITEM 1A. RISK
        # FACTORS") — a bleed in that style must still be cut.
        text = (
            "ITEM 1. BUSINESS\n"
            "We design and sell products worldwide.\n"
            "ITEM 1A. RISK FACTORS\n"
            "Bled risk-factor body.\n"
        )
        trimmed = parser._trim_section_text(text, "1")
        assert "ITEM 1A." not in trimmed
        assert "Bled risk-factor body" not in trimmed

    def test_item_keys_normalized_and_titled(self, store, fetch_calls):
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        risk = next(item for item in result.items if item.item == "1a")
        assert risk.title == "Risk Factors"
        assert "Risk Factors" in risk.text

    def test_duplicate_item_keys_keep_first_occurrence(self, store, fetch_calls):
        # Recorded reality: edgartools reports item 8 twice for AAPL FY2025
        # (part_ii_item_8 and a part_iv misattribution of the Notes).
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        eights = [item for item in result.items if item.item == "8"]
        assert len(eights) == 1
        assert _full_text(eights[0]).startswith("Item 8.")

    def test_degraded_section_shape_still_parses(self, store, monkeypatch):
        """UPGRADE GUARD (DEV-136 diagnosis; upstream root cause on DEV-147).

        edgartools names sections two ways: part-aware ("part_ii_item_7a",
        Section.item populated) and spaced ("Item 7A", Section.item None —
        observed live on MSFT/GE/DIS). The parser must not depend on the
        .item metadata alone: when it is missing, the item key derives from
        the section name. If an edgartools upgrade changes either shape,
        this test and its sibling below must both stay green.
        """
        prose = "The company operates in many segments worldwide. " * 20
        tenk = FakeTenK(
            sections_data={
                "Item 1": {"item": "", "text": f"Item 1. Business\n{prose}"},
                "Item 7A": {"item": "", "text": f"Item 7A. Market Risk\n{prose}"},
                "Signatures": {"item": "", "text": f"Signatures\n{prose}"},
            }
        )
        monkeypatch.setattr(
            parser, "fetch_filing_bundle", lambda *a, **k: make_bundle(tenk)
        )
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert [item.item for item in result.items] == ["1", "7a"]

    def test_part_aware_section_shape_still_parses(self, store, monkeypatch):
        """UPGRADE GUARD sibling: the part-aware shape (item populated,
        underscore names) keeps working unchanged."""
        prose = "The company operates in many segments worldwide. " * 20
        tenk = FakeTenK(
            sections_data={
                "part_i_item_1": {"item": "1", "text": f"Item 1. Business\n{prose}"},
                "part_ii_item_7a": {
                    "item": "7A",
                    "text": f"Item 7A. Market Risk\n{prose}",
                },
            }
        )
        monkeypatch.setattr(
            parser, "fetch_filing_bundle", lambda *a, **k: make_bundle(tenk)
        )
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert [item.item for item in result.items] == ["1", "7a"]

    def test_non_item_entries_skipped(self, store, monkeypatch):
        # A section with item=None (e.g. signatures) must not crash nor emit.
        tenk = FakeTenK(
            sections_data={
                "part_iv_signatures": {"item": "", "text": "Signatures. " * 20},
                "part_i_item_2": {"item": "2", "text": "Item 2. Properties. " * 20},
            }
        )
        monkeypatch.setattr(
            parser, "fetch_filing_bundle", lambda *a, **k: make_bundle(tenk)
        )
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert [item.item for item in result.items] == ["2"]

    def test_empty_text_item_skipped(self, store, monkeypatch):
        tenk = FakeTenK(
            sections_data={
                "part_i_item_1": {"item": "1", "text": "   \n  "},
                "part_i_item_2": {"item": "2", "text": "Item 2. Properties. " * 20},
            }
        )
        monkeypatch.setattr(
            parser, "fetch_filing_bundle", lambda *a, **k: make_bundle(tenk)
        )
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert [item.item for item in result.items] == ["2"]

    def test_all_sections_empty_or_stub_raises_and_saves_nothing(
        self, store, monkeypatch
    ):
        # A filing where every section is empty or a stub must fail loudly:
        # caching/returning an empty ParsedFiling would look like a
        # successful ingestion to every downstream consumer.
        tenk = FakeTenK(
            sections_data={
                "part_i_item_1": {"item": "1", "text": "   \n  "},
                "part_ii_item_6": {"item": "6", "text": "Item 6. [Reserved]"},
                "part_iii_item_11": {
                    "item": "11",
                    "text": (
                        "Item 11. Executive Compensation. The information "
                        "required by this Item is incorporated herein by "
                        "reference from the Proxy Statement."
                    ),
                },
            }
        )
        monkeypatch.setattr(
            parser, "fetch_filing_bundle", lambda *a, **k: make_bundle(tenk)
        )
        with pytest.raises(parser.EmptyFilingError) as excinfo:
            parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        # Actionable message: ticker, fiscal year, accession number.
        assert "AAPL" in str(excinfo.value)
        assert "2025" in str(excinfo.value)
        assert "0000320193-25-000079" in str(excinfo.value)
        assert store.get("AAPL", FilingType.TEN_K, 2025) is None


class TestDetectionWiring:
    def test_plausible_markdown_headings_upgrade_item_to_structured(
        self, store, monkeypatch, fake_bundle
    ):
        body = "Substantive business discussion line. " * 5
        tenk = FakeTenK(
            sections_data={
                "part_i_item_2": {
                    "item": "2",
                    "text": (
                        f"Item 2. Properties\nOwned Facilities\n{body}\n"
                        f"Leased Facilities\n{body}"
                    ),
                }
            }
        )
        monkeypatch.setattr(
            parser, "fetch_filing_bundle", lambda *a, **k: make_bundle(tenk)
        )
        monkeypatch.setattr(
            parser,
            "fetch_filing_markdown",
            lambda *a, **k: "### Owned Facilities\n### Leased Facilities\n",
        )
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        (item,) = result.items
        assert isinstance(item, StructuredItem)
        assert item.detection_source == "markdown_h3"
        assert [b.heading for b in item.blocks] == [
            "Owned Facilities",
            "Leased Facilities",
        ]
        assert item.prelude == "Item 2. Properties"  # verbatim, no carve-outs

    def test_structured_items_round_trip_through_store(
        self, store, monkeypatch, fake_bundle
    ):
        body = "Substantive business discussion line. " * 5
        tenk = FakeTenK(
            sections_data={
                "part_i_item_2": {
                    "item": "2",
                    "text": f"Item 2. Properties\nOwned\n{body}\nLeased\n{body}",
                }
            }
        )
        monkeypatch.setattr(
            parser, "fetch_filing_bundle", lambda *a, **k: make_bundle(tenk)
        )
        monkeypatch.setattr(
            parser, "fetch_filing_markdown", lambda *a, **k: "### Owned\n### Leased\n"
        )
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert store.get("AAPL", FilingType.TEN_K, 2025) == result


class TestMetadata:
    def test_metadata_from_filing_object(self, store, fetch_calls):
        meta = parser.parse_filing("AAPL", fiscal_year=2025, store=store).metadata
        assert meta.ticker == "AAPL"
        assert meta.cik == "320193"
        assert meta.company_name == "Apple Inc."
        assert meta.filing_type is FilingType.TEN_K
        assert meta.filing_date == "2025-10-31"
        assert meta.fiscal_year == 2025
        assert meta.accession_number == "0000320193-25-000079"
        assert meta.primary_document == "aapl-20250927.htm"
        assert meta.parsed_at  # timestamped

    def test_ticker_input_normalized(self, store, fetch_calls):
        meta = parser.parse_filing(" aapl ", fiscal_year=2025, store=store).metadata
        assert meta.ticker == "AAPL"
        assert fetch_calls[0][0] == "AAPL"


class TestStoreInteraction:
    def test_result_is_persisted_and_round_trips(self, store, fetch_calls):
        result = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert store.get("AAPL", FilingType.TEN_K, 2025) == result

    def test_cache_hit_skips_fetch(self, store, fetch_calls):
        first = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        second = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        assert second == first
        assert len(fetch_calls) == 1

    def test_force_bypasses_store_and_reparses(self, store, fetch_calls):
        # Pre-seed the store with a DIFFERENT ParsedFiling for the same key;
        # force=True must ignore it, hit the fetch seam, and overwrite it.
        seeded = ParsedFiling(
            metadata=make_metadata(fiscal_year=2025),
            items=[FlatItem(item="2", title="Properties", text="Stale seeded body.")],
        )
        store.save(seeded)

        result = parser.parse_filing("AAPL", fiscal_year=2025, force=True, store=store)

        assert len(fetch_calls) == 1  # store bypassed → fetch seam hit
        assert result != seeded
        assert {item.item for item in result.items} != {"2"}
        assert store.get("AAPL", FilingType.TEN_K, 2025) == result

    def test_default_store_is_local_sec_text(self, monkeypatch, tmp_path, fake_bundle):
        """Default store resolves via backend.common.data_paths — repo-root
        anchored, not CWD-relative. Chdir to a directory distinct from the
        SEC_TEXT_DIR override to prove CWD has no bearing on the resolved
        location, and use the env override so the test never writes into the
        real repo's data/ directory."""
        other_cwd = tmp_path / "elsewhere"
        other_cwd.mkdir()
        monkeypatch.chdir(other_cwd)
        target_dir = tmp_path / "sec_text_store"
        monkeypatch.setenv("SEC_TEXT_DIR", str(target_dir))
        monkeypatch.setattr(parser, "fetch_filing_bundle", lambda *a, **k: fake_bundle)
        parser.parse_filing("AAPL", fiscal_year=2025)
        assert (target_dir / "AAPL" / "10-K" / "2025.json").exists()


class TestErrorPropagationThroughParseFiling:
    """Fetch-stage errors must survive parse_filing untouched.

    parse_filing's docstring promises the FinLabError taxonomy propagates
    from fetch failures; these tests pin the two SEC-specific members
    (FilingNotFoundError, UnsupportedFilingTypeError) at the public seam —
    exact type (distinguishable by an API layer), message intact, and the
    failure happens before the markdown fetch (the detection-stage call
    inserted between bundle fetch and item parsing must not reorder or
    swallow fetch errors). EmptyFilingError's leg of the same contract is
    covered by test_all_sections_empty_or_stub_raises_and_saves_nothing.
    """

    @pytest.mark.parametrize(
        "exc_type,message",
        [
            (
                FilingNotFoundError,
                "No 10-K filing for AAPL in fiscal year 2025.",
            ),
            (
                UnsupportedFilingTypeError,
                "Ticker AAPL appears to be a foreign private issuer that "
                "files 20-F; only '10-K' is supported.",
            ),
        ],
    )
    def test_fetch_errors_propagate_with_exact_type_and_message(
        self, store, monkeypatch, exc_type, message
    ):
        def raising_fetch(*args, **kwargs):
            raise exc_type(message)

        monkeypatch.setattr(parser, "fetch_filing_bundle", raising_fetch)
        markdown_calls: list[tuple] = []
        monkeypatch.setattr(
            parser,
            "fetch_filing_markdown",
            lambda *a, **k: markdown_calls.append(a) or "",
        )

        with pytest.raises(exc_type) as excinfo:
            parser.parse_filing("AAPL", fiscal_year=2025, store=store)

        assert type(excinfo.value) is exc_type  # not a SECError sibling
        assert str(excinfo.value) == message  # ticker/year context intact
        assert markdown_calls == []  # failed before the markdown fetch


class TestForceRerunFailureLeavesStoreIntact:
    """force=True re-runs that fail must not touch the previously saved
    parse — the new attempt aborts before its single store.save() call, so
    the good result from the earlier run stays byte-identical on disk."""

    def _seed_success(self, store, tmp_path, monkeypatch, fake_bundle):
        monkeypatch.setattr(parser, "fetch_filing_bundle", lambda *a, **k: fake_bundle)
        first = parser.parse_filing("AAPL", fiscal_year=2025, store=store)
        saved_file = next(tmp_path.rglob("*.json"))
        return first, saved_file, saved_file.read_bytes()

    def test_empty_filing_failure_preserves_previous_result(
        self, store, tmp_path, monkeypatch, fake_bundle
    ):
        first, saved_file, bytes_before = self._seed_success(
            store, tmp_path, monkeypatch, fake_bundle
        )

        all_stub = FakeTenK(
            sections_data={
                "part_ii_item_6": {"item": "6", "text": "Item 6. [Reserved]"}
            }
        )
        monkeypatch.setattr(
            parser, "fetch_filing_bundle", lambda *a, **k: make_bundle(all_stub)
        )
        with pytest.raises(parser.EmptyFilingError):
            parser.parse_filing("AAPL", fiscal_year=2025, force=True, store=store)

        assert saved_file.read_bytes() == bytes_before
        assert store.get("AAPL", FilingType.TEN_K, 2025) == first

    def test_markdown_fetch_failure_preserves_previous_result(
        self, store, tmp_path, monkeypatch, fake_bundle
    ):
        # The markdown fetch is the failure point THIS slice added to
        # parse_filing — it sits before store.save(), so a render failure on
        # a forced re-run must leave the earlier good parse untouched.
        first, saved_file, bytes_before = self._seed_success(
            store, tmp_path, monkeypatch, fake_bundle
        )

        def failing_markdown(*args, **kwargs):
            raise SECError("Failed to render markdown for AAPL 10-K")

        monkeypatch.setattr(parser, "fetch_filing_markdown", failing_markdown)
        with pytest.raises(SECError):
            parser.parse_filing("AAPL", fiscal_year=2025, force=True, store=store)

        assert saved_file.read_bytes() == bytes_before
        assert store.get("AAPL", FilingType.TEN_K, 2025) == first
