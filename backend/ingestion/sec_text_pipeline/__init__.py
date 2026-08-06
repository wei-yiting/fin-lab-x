"""SEC text pipeline — structured 10-K parsing on edgartools' section API.

Replaces the parse stage of the frozen HTML pipeline (A/B baseline): Item
boundaries come from edgartools sections instead of HTML heuristics, and the
output is a typed :class:`ParsedFiling` (no markdown intermediate).

Public surface: :func:`parse_filing` plus the ParsedFiling schema types.
"""

from backend.ingestion.sec_text_pipeline.filing_models import (
    Block,
    FilingMetadata,
    FlatItem,
    ParsedFiling,
    ParsedItem,
    StructuredItem,
)
from backend.ingestion.sec_text_pipeline.parser import parse_filing

__all__ = [
    "Block",
    "FilingMetadata",
    "FlatItem",
    "ParsedFiling",
    "ParsedItem",
    "StructuredItem",
    "parse_filing",
]
