"""ParsedFiling schema — the frozen contract of the SEC text pipeline.

Design source: DEV-127 spec + design.md §3. The schema is fixed in this
module and downstream tickets (markdown detection, dense ingest, inspect
view) build against it without changes.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from backend.common.sec_core import FilingType


class FilingMetadata(BaseModel):
    """Filing-level metadata, including the citation-chain source fields.

    ``accession_number`` / ``cik`` / ``primary_document`` feed the DEV-125
    citation data chain: stable chunk IDs and mechanically-derived EDGAR
    URLs at the API/frontend boundary. No URL is stored anywhere — it is
    always derived from these three fields.
    """

    ticker: str
    cik: str
    company_name: str
    filing_type: FilingType
    filing_date: str
    fiscal_year: int
    accession_number: str
    primary_document: str
    parsed_at: str


class Block(BaseModel):
    """A heading-delimited span of an Item's body (plain text)."""

    heading: str
    text: str


class StructuredItem(BaseModel):
    """An Item whose block structure was detected.

    ``detection_source`` records which of the three detection paths found
    the blocks (A/B sampling axis + failure attribution; filing store and
    inspect view only — never a Qdrant payload field).
    """

    kind: Literal["structured"] = "structured"
    item: str
    title: str
    prelude: str
    blocks: list[Block] = Field(min_length=1)
    detection_source: Literal["markdown_h3", "markdown_h4", "text_fallback"]


class FlatItem(BaseModel):
    """An Item with no detected block structure — the whole body as one text."""

    kind: Literal["flat"] = "flat"
    item: str
    title: str
    text: str


ParsedItem = Annotated[StructuredItem | FlatItem, Field(discriminator="kind")]


class ParsedFiling(BaseModel):
    """Typed parse result for one filing. Stub items are already dropped."""

    metadata: FilingMetadata
    items: list[ParsedItem]
