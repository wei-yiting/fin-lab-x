import pytest

from backend.common.sec_core import is_stub_section
from backend.ingestion.sec_text_pipeline.stub_detection import is_stub_section_v2

# Condensed from the real pseudo-stub bodies that motivated R8 (design.md
# §4.6): items whose entire substance is a pointer to elsewhere in the
# annual report — invisible to the v1 incorporated-by-reference pattern.
JPM_ITEM_7_STYLE = (
    "Item 7. Management's discussion and analysis of financial condition "
    "and results of operations. Management's discussion and analysis of "
    "the financial condition and results of operations, entitled "
    "Management's discussion and analysis, appears on pages 46-160 of the "
    "Annual Report."
)

JPM_ITEM_7A_STYLE = (
    "Item 7A. Quantitative and qualitative disclosures about market risk. "
    "Refer to the Market Risk Management section on pages 124-131 of the "
    "Annual Report."
)

XOM_ITEM_7_STYLE = (
    "Item 7. Management's Discussion and Analysis of Financial Condition "
    "and Results of Operations. Reference is made to the section entitled "
    "Financial Review incorporated herein from pages 38 to 55 of the "
    "Annual Report."
)


@pytest.mark.parametrize(
    "text",
    [JPM_ITEM_7_STYLE, JPM_ITEM_7A_STYLE, XOM_ITEM_7_STYLE],
    ids=[
        "jpm_7_appears_on_pages",
        "jpm_7a_refer_to_section",
        "xom_7_reference_is_made",
    ],
)
def test_pseudo_stub_pointer_items_are_dropped(text):
    is_stub, reason = is_stub_section_v2(text)
    assert is_stub is True
    assert reason is not None


def test_large_mda_with_pointer_sentence_survives():
    # R8 red line: v2 patterns must run through the remove-matching-
    # sentences-then-measure-remainder mechanism, never "phrase => stub".
    # A real MD&A casually saying "Reference is made to Note 12" keeps
    # tens of thousands of chars of substance after the pointer sentence
    # is dropped — it must NOT classify as a stub.
    paragraph = (
        "Net revenue increased 12% year over year, driven by growth in "
        "subscription services and expansion in international segments. "
        "Operating expenses grew at a slower pace as we realized benefits "
        "from infrastructure efficiency initiatives launched last year. "
    )
    mda = (
        "Item 7. Management's Discussion and Analysis. "
        "Reference is made to Note 12 of the consolidated financial "
        "statements for further discussion of commitments. " + paragraph * 250
    )
    assert len(mda) > 60_000
    assert is_stub_section_v2(mda) == (False, None)


def test_v2_still_catches_v1_incorp_stub():
    text = (
        "Item 11. The information required by this Item is incorporated "
        "herein by reference from the Proxy Statement."
    )
    is_stub, reason = is_stub_section_v2(text)
    assert is_stub is True
    assert "incorporated" in reason


def test_v2_still_catches_reserved_item():
    is_stub, reason = is_stub_section_v2("Item 6. [Reserved]")
    assert is_stub is True
    assert "reserved" in reason


def test_v1_does_not_know_pseudo_stub_patterns():
    # Coexistence guarantee: the frozen v1 classifier must remain blind to
    # the v2-only patterns (production behavior unchanged during A/B).
    assert is_stub_section(JPM_ITEM_7_STYLE) == (False, None)
    assert is_stub_section(JPM_ITEM_7A_STYLE) == (False, None)


def test_multiple_pointer_sentences_all_removed_before_measuring():
    # An item made of several pointer sentences (mixed patterns) and
    # nothing else is still a stub — every matching sentence is removed,
    # not just the first.
    text = (
        "Item 7A. Reference is made to the Market Risk section. "
        "Refer to the Liquidity section for funding risk. "
        "The remainder appears on pages 88-90 of the Annual Report."
    )
    assert is_stub_section_v2(text)[0] is True
