import tiktoken
import pytest
from backend.ingestion.sec_dense_pipeline.vectorizer import parse_item, create_text_splitter


@pytest.mark.parametrize("raw_path,expected_item", [
    ("Item 1 / Business", "Item 1"),
    ("Item 1A / Risks Related to Our Industry", "Item 1A"),
    ("Item 7 / MD&A / Critical Accounting", "Item 7"),
    ("Item 7A / Quantitative Disclosures", "Item 7A"),
    ("Item 9A(T) / Controls and Procedures", "Item 9A(T)"),
    ("Item 1A. Risk Factors", "Item 1A"),
    ("PART I", "_unknown"),
    ("", "_unknown"),
    ("NVDA / 2025 / Item 1A / Risks", "Item 1A"),
    ("Part I / Item 1A. Risk Factors", "Item 1A"),
    ("Part II / Item 7. MD&A", "Item 7"),
])
def test_parse_item(raw_path: str, expected_item: str) -> None:
    assert parse_item(raw_path) == expected_item


def test_splitter_uses_tiktoken_not_charcount() -> None:
    enc = tiktoken.get_encoding("cl100k_base")
    words = ["financial"] * 1400
    text = " ".join(words)

    splitter = create_text_splitter()
    chunks = splitter.split_text(text)

    assert len(chunks) <= 6, (
        f"Expected ~4 chunks, got {len(chunks)} — likely character-mode splitting"
    )
    assert len(chunks) >= 3, (
        f"Expected ~4 chunks, got {len(chunks)} — might not be splitting at all"
    )

    for chunk in chunks:
        token_count = len(enc.encode(chunk))
        assert token_count <= 512, f"Chunk has {token_count} tokens, exceeds 512"
