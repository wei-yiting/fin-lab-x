"""ParsedFiling schema — the frozen contract of the SEC text pipeline.

The schema is fixed in this module and downstream stages (markdown block
detection, dense ingest, the inspect view) build against it without
changes. Every model forbids unknown fields: the filing store persists
these models as JSON, and a silently-discarded field would mean stored
data and schema had drifted apart without anyone noticing.

One ratified change (ADR-0018 degraded ingest): ``ParsedFiling.degraded_text``
and ``FilingMetadata.section_detection_method`` were added for filings whose
upstream section detection ran degraded. Both are additive with defaults, so
JSON stored before the change still validates.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.common.sec_core import FilingType


class FilingMetadata(BaseModel):
    """Filing-level metadata, including the citation-chain source fields.

    ``accession_number`` / ``cik`` / ``primary_document`` feed the citation
    data chain: stable chunk IDs and mechanically-derived EDGAR URLs at the
    API/frontend boundary. No URL is stored anywhere — it is always derived
    from these three fields.
    """

    model_config = ConfigDict(extra="forbid")

    ticker: str
    cik: str
    company_name: str
    filing_type: FilingType
    filing_date: str
    fiscal_year: int
    accession_number: str
    primary_document: str
    parsed_at: str
    #: Upstream section detection method, passed through from edgartools
    #: (single strategy per filing: "toc" / "heading" / "pattern" /
    #: "unknown"...). "" means the filing was parsed before this field
    #: existed — distinct from "unknown", which is a real observation.
    section_detection_method: str = ""


class Block(BaseModel):
    """A heading-delimited span of an Item's body (plain text)."""

    model_config = ConfigDict(extra="forbid")

    heading: str
    text: str


class StructuredItem(BaseModel):
    """An Item whose block structure was detected.

    ``detection_source`` records which of the three detection paths found
    the blocks (A/B sampling axis + failure attribution; filing store and
    inspect view only — never a Qdrant payload field).
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["structured"] = "structured"
    item: str
    title: str
    prelude: str
    blocks: list[Block] = Field(min_length=1)
    detection_source: Literal["markdown_h3", "markdown_h4", "text_fallback"]


class FlatItem(BaseModel):
    """An Item with no detected block structure — the whole body as one text."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["flat"] = "flat"
    item: str
    title: str
    text: str


ParsedItem = Annotated[StructuredItem | FlatItem, Field(discriminator="kind")]


class ParsedFiling(BaseModel):
    """Typed parse result for one filing. Stub items are already dropped.

    A degraded filing (section detection ran a fallback strategy the item
    parser cannot trust — ADR-0018) carries the noise-cleaned full document
    text in ``degraded_text`` and an empty ``items`` list; a standard
    filing has items and ``degraded_text is None``. The parser owns that
    invariant — the schema deliberately does not enforce it (failure
    legibility is the parser's job, not the model's).
    """

    model_config = ConfigDict(extra="forbid")

    metadata: FilingMetadata
    items: list[ParsedItem]
    degraded_text: str | None = None

    @property
    def is_degraded(self) -> bool:
        """True when this filing was ingested via the degraded path."""
        return self.degraded_text is not None
