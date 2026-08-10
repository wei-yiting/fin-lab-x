"""Structure-aware chunking over :class:`ParsedFiling` for the dense pipeline.

Chunk boundaries never cross a block boundary: each block (and each FlatItem
body, and each reclassified heading-less leading block) is split
independently, so overlap only ever connects adjacent chunks of the same
block. ``chunk_index`` runs over the whole filing — it is the fragment of the
citation stable ID ``sec://{accession_number}/{item}#{chunk_index}``, so it
must be unique per filing, not per block.

A valid prelude is attached whole to every chunk payload of its Item (never
chunked or embedded on its own — retrieve-time context comes straight from
the payload). ``prelude`` / ``block_heading`` are ``None`` in the payload
whenever the schema carries no such text: FlatItems have neither, and a
reclassified leading block (schema ``prelude == ""``, ``heading == ""``) has
its text in the chunk flow instead of the metadata.
"""

from __future__ import annotations

import os
from typing import Any
from uuid import NAMESPACE_DNS, uuid5

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.ingestion.sec_dense_pipeline.common import canonicalize_ticker
from backend.ingestion.sec_text_pipeline.filing_models import (
    FlatItem,
    ParsedFiling,
)


def create_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=int(os.environ.get("SEC_CHUNK_SIZE", "512")),
        chunk_overlap=int(os.environ.get("SEC_CHUNK_OVERLAP", "50")),
    )


def chunk_point_id(ticker: str, fiscal_year: int, chunk_index: int) -> str:
    """Deterministic Qdrant point ID for one chunk of one filing."""
    return str(uuid5(NAMESPACE_DNS, f"{ticker}:{fiscal_year}:{chunk_index}"))


def build_chunk_payloads(filing: ParsedFiling) -> list[dict[str, Any]]:
    """Chunk a filing into the full new-contract Qdrant payloads.

    Pure function: no I/O, no embeddings. The vectorizer stamps
    ``ingested_at`` and derives point IDs from ``chunk_index`` at upsert
    time.
    """
    meta = filing.metadata
    ticker = canonicalize_ticker(meta.ticker)
    splitter = create_text_splitter()

    payloads: list[dict[str, Any]] = []
    chunk_index = 0
    for item in filing.items:
        item_label = f"Item {item.item.upper()}. {item.title}"
        base_path = f"{ticker} / {meta.fiscal_year} / {item_label}"

        # (block_heading, prelude, text) units feeding the chunk flow.
        units: list[tuple[str | None, str | None, str]]
        if isinstance(item, FlatItem):
            units = [(None, None, item.text)]
        else:
            prelude = item.prelude or None
            units = [
                (block.heading or None, prelude, block.text) for block in item.blocks
            ]

        for block_heading, prelude, text in units:
            header_path = (
                f"{base_path} / {block_heading}" if block_heading else base_path
            )
            for piece in splitter.split_text(text):
                payloads.append(
                    {
                        "ticker": ticker,
                        "fiscal_year": meta.fiscal_year,
                        "filing_date": meta.filing_date,
                        "filing_type": str(meta.filing_type),
                        "accession_number": meta.accession_number,
                        "cik": meta.cik,
                        "primary_document": meta.primary_document,
                        "item": item.item,
                        "block_heading": block_heading,
                        "prelude": prelude,
                        "header_path": header_path,
                        "chunk_index": chunk_index,
                        "text": piece,
                    }
                )
                chunk_index += 1
    return payloads
