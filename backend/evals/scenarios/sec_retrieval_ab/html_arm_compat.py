"""Frozen-HTML-arm compatibility layer for the sec_retrieval_ab A/B scenario.

The frozen HTML pipeline's real retrieved chunks (backend/ingestion/sec_dense_pipeline_html/
vectorizer.py) carry a header_path shape that isn't directly comparable to the new text
pipeline's Item-level contract (TICKER / fiscal year / Item N. Title, no Part): the HTML arm's
header_path may include a Part segment, and its title text is extracted live from each
filing's own HTML rather than a fixed dictionary — sometimes matching the canonical title,
sometimes diverging from it (curly vs. straight apostrophes, "and" vs. a comma), in ways
scattered across tickers and Items that no single string-repair rule could generalize.

normalize_chunk / normalize_chunks rebuild the Item segment from scratch — from the chunk's
own already-parsed `item` field, the chunk's own `ticker`/`year` fields, and the canonical
title in backend.common.sec_core.TENK_STANDARD_TITLES — rather than editing the pipeline's
live-extracted title text. Any content nested below the Item level (block-level headings) is
left untouched: the sec_retrieval scorer's hit logic is `header_path.startswith(expected)`, so
a longer tail after the rebuilt Item segment doesn't break the comparison, and keeping it
preserves debugging detail. A chunk whose item couldn't be detected at all (`"_unknown"`, or
any value that doesn't resolve to a known canonical title) is returned unchanged — that's a
real detection failure in the frozen pipeline, and it should honestly surface as a scoring miss
rather than being papered over.

Chunk text is passed through unchanged. Investigation during design found no evidence of a
real character-level or whitespace divergence between the two pipelines' body text — the one
confirmed divergence (title-text formatting) is fully handled by the header_path rebuild above.
The scorer's existing case-insensitive substring check already covers case differences
symmetrically for both arms. One known edge case is deliberately not addressed here: financial
tables render as structurally different text between the two pipelines (pipe-delimited markdown
vs. plain text with no cell separators), which could make a table-derived ground-truth snippet
fail to match. This is not fixed because (a) the scorer's snippet check is substring
containment, so it only matters when the snippet's own text falls inside a table, and (b) the
shared dataset's snippet contract requires a single complete sentence, which makes that
combination very unlikely in practice. If a future measurement run finds real evidence of a
text-matching gap, add a normalization step here then, backed by the specific failing case —
don't extend this speculatively.

This module intentionally never modifies backend.evals.scenarios.sec_retrieval.scorer: that
scorer is live and gates the production regression suite, and all frozen-HTML-specific
compatibility logic is isolated here instead of branching inside code other scenarios depend
on. It has no dependency on the sec_retrieval_ab scenario's dataset or eval_spec.yaml existing.

This module is scoped to the frozen HTML pipeline's lifetime and is deleted alongside it at
sunset — see AGENTS.md's "Ingestion Rewrite Coexistence" section. Its design
rationale lives here rather than in an ADR or a CONTEXT.md glossary entry precisely because
both are meant to outlive the thing they describe, and this doesn't.
"""

import re

from backend.common.sec_core import TENK_STANDARD_TITLES

_ITEM_SEGMENT_RE = re.compile(r"^(Item \d+[A-Z]?(?:\(T\))?)\.?")


def normalize_chunk(chunk: dict) -> dict:
    """Rebuild a frozen-HTML-arm chunk's header_path into the new pipeline's Item-level shape.

    Returns a new dict; `chunk` is never mutated. `text` and every other field pass through
    unchanged — only `header_path` is ever rewritten.
    """
    item = chunk.get("item", "_unknown")
    if item == "_unknown":
        return dict(chunk)

    canonical_title = TENK_STANDARD_TITLES.get(item[len("Item ") :].lower())
    if canonical_title is None:
        return dict(chunk)

    segments = chunk["header_path"].split(" / ")
    item_index = next(
        (
            i
            for i, segment in enumerate(segments)
            if (match := _ITEM_SEGMENT_RE.match(segment)) and match.group(1) == item
        ),
        None,
    )
    if item_index is None:
        return dict(chunk)

    tail = segments[item_index + 1 :]
    rebuilt_path = f"{chunk['ticker']} / {chunk['year']} / {item}. {canonical_title}"
    if tail:
        rebuilt_path += " / " + " / ".join(tail)

    return {**chunk, "header_path": rebuilt_path}


def normalize_chunks(chunks: list[dict]) -> list[dict]:
    """normalize_chunk mapped over a list — the shape output["retrieved_chunks"] expects."""
    return [normalize_chunk(chunk) for chunk in chunks]
