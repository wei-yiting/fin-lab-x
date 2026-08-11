"""Structure-aware chunking over :class:`ParsedFiling` for the dense pipeline.

Chunk boundaries never cross a block boundary: each block (and each FlatItem
body, and each reclassified heading-less leading block) is split
independently, so overlap only ever connects adjacent chunks of the same
block. ``chunk_index`` runs over the whole filing — it is the fragment of the
citation stable ID ``sec://{accession_number}/{item}#{chunk_index}``, so it
must be unique per filing, not per block.

A valid prelude enters the chunk flow twice-over: it produces its own
heading-less leading chunk(s) — same path and same payload shape as a
FlatItem body or a reclassified leading block, so financial content that
lands in a prelude stays searchable — and it is additionally attached whole
to every *block* chunk payload of its Item as retrieve-time context. The
DEV-133 validity threshold governs only that metadata attachment, never
search visibility. ``prelude`` / ``block_heading`` are ``None`` on every
leading chunk (prelude-own, FlatItem, reclassified) and on block chunks of
items without a valid prelude.
"""

from __future__ import annotations

import os
from typing import NotRequired, TypedDict
from uuid import NAMESPACE_DNS, uuid5

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.ingestion.sec_dense_pipeline.common import canonicalize_ticker
from backend.ingestion.sec_text_pipeline.filing_models import (
    FlatItem,
    ParsedFiling,
)


class ChunkPayload(TypedDict):
    """Qdrant payload schema for one content chunk.

    ``ingested_at`` is stamped by the vectorizer at upsert time; every other
    field is produced by :func:`build_chunk_payloads`.
    """

    ticker: str
    fiscal_year: int
    filing_date: str
    filing_type: str
    accession_number: str
    cik: str
    primary_document: str
    item: str
    block_heading: str | None
    prelude: str | None
    header_path: str
    chunk_index: int
    text: str
    ingested_at: NotRequired[str]


def create_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=int(os.environ.get("SEC_CHUNK_SIZE", "512")),
        chunk_overlap=int(os.environ.get("SEC_CHUNK_OVERLAP", "50")),
    )


def chunk_point_id(ticker: str, fiscal_year: int, chunk_index: int) -> str:
    """Deterministic Qdrant point ID for one chunk of one filing."""
    return str(uuid5(NAMESPACE_DNS, f"{ticker}:{fiscal_year}:{chunk_index}"))


def build_chunk_payloads(filing: ParsedFiling) -> list[ChunkPayload]:
    """Chunk a filing into the full new-contract Qdrant payloads.

    Pure function: no I/O, no embeddings. The vectorizer stamps
    ``ingested_at`` and derives point IDs from ``chunk_index`` at upsert
    time.
    """
    meta = filing.metadata
    ticker = canonicalize_ticker(meta.ticker)
    splitter = create_text_splitter()

    payloads: list[ChunkPayload] = []
    chunk_index = 0
    for item in filing.items:
        # Normalize once at the contract boundary: the schema's `item` is an
        # unconstrained str, but the payload `item` index/filter contract is
        # the lowercase stripped key (e.g. "7a").
        item_key = item.item.strip().lower()
        item_label = f"Item {item_key.upper()}. {item.title}"
        base_path = f"{ticker} / {meta.fiscal_year} / {item_label}"

        # (block_heading, prelude, text) units feeding the chunk flow.
        units: list[tuple[str | None, str | None, str]]
        if isinstance(item, FlatItem):
            units = [(None, None, item.text)]
        else:
            prelude = item.prelude or None
            units = []
            if prelude:
                # The prelude's own searchable leading chunk: handled exactly
                # like a FlatItem body / reclassified leading block, so its
                # own payload carries prelude=None (it IS the prelude).
                units.append((None, None, prelude))
            units += [
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
                        "item": item_key,
                        "block_heading": block_heading,
                        "prelude": prelude,
                        "header_path": header_path,
                        "chunk_index": chunk_index,
                        "text": piece,
                    }
                )
                chunk_index += 1
    return payloads
