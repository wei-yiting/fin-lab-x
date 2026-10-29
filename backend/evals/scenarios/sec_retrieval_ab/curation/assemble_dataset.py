"""Round-3 task T7: emit the final dataset.csv from the round-2 ticker results.

Inputs are the per-ticker traversal results (`round2_ticker_results/*.json`,
already re-anchored to the filing store by T1–T6) plus the human-approved
outcome of the round-2 two-reviewer reconciliation (`round2_reconciliation.md`),
encoded below as explicit decision tables. Every emitted location is resolved
against the filing store, so header paths, block headings and detection
sources come from the store, never from the curation JSON's free-text hints.

Usage:
    uv run python -m backend.evals.scenarios.sec_retrieval_ab.curation.assemble_dataset
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.evals.scenarios.sec_retrieval_ab.curation.ingest_tickers import (
    TICKER_GRID,
)
from backend.evals.scenarios.sec_retrieval_ab.curation.validate_dataset import (
    load_csv_rows,
    load_filings,
    validate_rows,
)
from backend.ingestion.sec_text_pipeline.filing_models import (
    FlatItem,
    ParsedFiling,
    StructuredItem,
)

CURATION_DIR = Path(__file__).parent
DATASET_PATH = CURATION_DIR.parent / "dataset.csv"

DATASET_COLUMNS = [
    "question",
    "expected_header_paths",
    "expected_tickers",
    "match_mode",
    "answer_snippets",
    "query_type",
    "answer_spans",
    "block_heading",
    "detection_source",
    "sector",
    "market_cap_bucket",
    "generation_mode",
    "user_intent",
    "curation_note",
    "generated_by",
    "fiscal_year",
    "accession_number",
    "candidate_id",
    "answer_requirement",
    "review_provenance",
]

ROUND1_GENERATOR = "gpt-5.6-sol"
ROUND2_GENERATOR = "round2-curation-agent"

# Both independent LLM reviewers approved these unchanged.
BOTH_APPROVED = (
    "p20 p38 p41 p43 p44 p48 p49 p16 p17 p22 p24 p26 p29 p30 p32 p34 p35 "
    "a16 a17 a18 a23 n01 n04 n09 n10"
).split()

# Fixes the user approved from the reconciliation (G1 = both reviewers agreed
# on the fix; G3 = reviewer A only, mechanical fixes).
FIXED = {
    "p45": "G1",
    "a24": "G1",
    "a25": "G1",
    "n05": "G1",
    "a19": "G1",
    "p37": "G3",
    "a20": "G3",
    "a21": "G3",
    "p21": "G3",
    "p18": "G3",
    "p33": "G3",
    "a22": "G3",
    "p36": "G3",
    "p23": "G3",
    "n08": "G3",
}

QUESTION_REWRITES: dict[str, tuple[str, str | None]] = {
    # candidate_id: (question, answer_requirement or None to keep)
    "p45": (
        "How much debt principal did Datadog raise through its 2029 Notes issuance?",
        "One independently sufficient span must state the $1.0 billion aggregate "
        "principal amount of Datadog's 2029 Notes.",
    ),
    "a24": (
        "When do Alphabet's revolving credit lines expire?",
        "One independently sufficient span must state when Alphabet's revolving "
        "credit facilities expire (April 2026 and April 2030).",
    ),
    "a25": (
        "What purchase price did Caterpillar expect to pay for RPMGlobal?",
        "One independently sufficient span must state the expected purchase price "
        "of approximately $790 million for Caterpillar's RPMGlobal acquisition.",
    ),
    "p37": ("What consumer hardware products does Amazon make?", None),
    "a20": ("What investments drove Insulet's higher capital spending in 2025?", None),
    "a21": (
        "Does Coinbase actively trade the crypto it keeps on its balance sheet "
        "as an investment?",
        None,
    ),
    "p21": (
        "What kind of revenue does Coinbase mostly earn from non-US customers?",
        None,
    ),
    "p18": ("Could U.S. export controls delay or cost Datadog customer deals?", None),
}

QUERY_TYPE_OVERRIDES = {"p33": "passage"}

DROPPED_OCCURRENCES = {
    "n05": {"COST-2025-083984", "COST-2025-084633"},
    "a19": {"LLY-2025-081769", "LLY-2025-202988"},
}


@dataclass(frozen=True)
class EvidenceEdit:
    """Replace an occurrence's span and/or snippet with store-exact text.

    `span_start` extends the span backwards to the store text beginning with
    that phrase (same unit), keeping the original span's end.
    """

    span_start: str | None = None
    span: str | None = None
    snippet: str | None = None


EVIDENCE_EDITS: dict[str, EvidenceEdit] = {
    # Spans that did not name their subject now include the antecedent sentence.
    "NVDA-2026-023747": EvidenceEdit(
        span_start="In fiscal year 2026, we unveiled the NVIDIA Rubin platform"
    ),
    "AMZN-2025-119988": EvidenceEdit(
        span_start="We currently expense the majority of the costs associated with"
    ),
    "PODD-2025-014411": EvidenceEdit(
        span_start="The Pod integrates with a third-party continuous glucose monitor"
    ),
    # Snippets that crossed a paragraph break, trimmed to the break.
    "DECK-2026-160539": EvidenceEdit(
        span="We experienced an increase of 6.2% in the total volume of units sold "
        "to 78,700 from 74,100,",
        snippet="We experienced an increase of 6.2% in the total volume of units sold "
        "to 78,700 from 74,100,",
    ),
    "DECK-2026-014599": EvidenceEdit(
        span="under three proprietary brands: HOKA, UGG, and Teva.",
        snippet="under three proprietary brands: HOKA, UGG, and Teva.",
    ),
}

# Known gaps the store-anchored contract cannot express, recorded per row.
LOCATION_NOTES = {
    "n08": "The same brand sentence also appears in Item 7, but the filing store "
    "parses it there as block headings (text_fallback misdetection), so no "
    "store-exact Item 7 span exists; an arm that retrieves the Item 7 copy "
    "scores a miss.",
}


@dataclass(frozen=True)
class Location:
    header_path: str
    span: str
    snippet: str
    block_heading: str | None
    detection_source: str


def _units(item: StructuredItem | FlatItem) -> list[tuple[str | None, str]]:
    if isinstance(item, FlatItem):
        return [(None, item.text)]
    units: list[tuple[str | None, str]] = []
    if item.prelude:
        units.append((None, item.prelude))
    units.extend((block.heading, block.text) for block in item.blocks)
    return units


def _item_key(occurrence: dict[str, Any]) -> str:
    anchor = occurrence.get("store_anchor") or {}
    raw = anchor.get("item") or occurrence["item_hint"]
    match = re.match(r"\s*(?:item\s*)?(\d+[a-z]?)", str(raw), re.IGNORECASE)
    if match is None:
        raise ValueError(f"cannot parse item from {raw!r}")
    return match.group(1).lower()


def _resolve(
    filing: ParsedFiling, occurrence: dict[str, Any], edit: EvidenceEdit | None
) -> Location:
    item_key = _item_key(occurrence)
    item = next(i for i in filing.items if i.item.strip().lower() == item_key)
    span = occurrence["answer_span"]
    snippet = occurrence["answer_snippet"]
    if edit is not None:
        span = edit.span or span
        snippet = edit.snippet or snippet
    for heading, text in _units(item):
        lowered = text.lower()
        pos = lowered.find(span.lower())
        if pos < 0:
            continue
        if edit is not None and edit.span_start is not None:
            start = text.rfind(edit.span_start, 0, pos + 1)
            if start < 0:
                raise ValueError(f"{occurrence['occurrence_id']}: span_start not found")
            span = text[start : pos + len(span)]
        meta = filing.metadata
        detection = "flat" if isinstance(item, FlatItem) else str(item.detection_source)
        return Location(
            header_path=(
                f"{meta.ticker.upper()} / {meta.fiscal_year} / "
                f"Item {item.item.strip().upper()}. {item.title}"
            ),
            span=span,
            snippet=snippet,
            block_heading=heading,
            detection_source=detection,
        )
    raise ValueError(
        f"{occurrence['occurrence_id']}: span not found in Item {item_key}"
    )


def _load_results() -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for path in sorted((CURATION_DIR / "round2_ticker_results").glob("T*.json")):
        ticker_result = json.loads(path.read_text(encoding="utf-8"))
        for candidate in ticker_result["candidate_results"]:
            candidate["_ticker"] = ticker_result["ticker"]
            candidate["_fiscal_year"] = int(ticker_result["fiscal_year"])
            candidate["_accession"] = ticker_result["source"]["accession_number"]
            results[candidate["candidate_id"]] = candidate
    return results


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _provenance(candidate_id: str, dropped: set[str]) -> str:
    if candidate_id not in FIXED:
        return "Round 2: approved unchanged by both independent LLM reviewers."
    parts = [f"Round 2: reconciliation {FIXED[candidate_id]} fix approved by the user"]
    if candidate_id in QUESTION_REWRITES:
        parts.append("question rewritten")
    if dropped:
        parts.append("dropped " + ", ".join(sorted(dropped)))
    if candidate_id in QUERY_TYPE_OVERRIDES:
        parts.append(f"query_type -> {QUERY_TYPE_OVERRIDES[candidate_id]}")
    provenance = "; ".join(parts) + "."
    provenance += (
        " Post-fix re-review by reviewer B (curation/round3_llm_review_codex.csv):"
        " approved."
    )
    if candidate_id in LOCATION_NOTES:
        provenance += " " + LOCATION_NOTES[candidate_id]
    return provenance


def build_rows(filings: dict[tuple[str, int], ParsedFiling]) -> list[dict[str, str]]:
    results = _load_results()
    review = {
        r["candidate_id"]: r for r in _read_csv(CURATION_DIR / "round2_review.csv")
    }
    intents = {
        r["candidate_id"]: r
        for r in _read_csv(CURATION_DIR / "round2_intent_first_questions.csv")
    }
    selected = set(BOTH_APPROVED) | set(FIXED)
    rows: list[dict[str, str]] = []
    for candidate_id, review_row in review.items():
        if candidate_id not in selected:
            continue
        candidate = results[candidate_id]
        ticker = candidate["_ticker"]
        filing = filings[(ticker, candidate["_fiscal_year"])]
        dropped = DROPPED_OCCURRENCES.get(candidate_id, set())
        occurrences = [
            o
            for o in candidate["acceptable_occurrences"]
            if o["occurrence_id"] not in dropped
        ]
        locations = [
            _resolve(filing, o, EVIDENCE_EDITS.get(o["occurrence_id"]))
            for o in occurrences
        ]

        proposal = candidate["proposal"]
        question, requirement = QUESTION_REWRITES.get(candidate_id, (None, None))
        is_new = candidate_id.startswith("n")
        intent = (
            intents[candidate_id]["investor_intent"]
            if is_new
            else (candidate.get("round1") or {}).get("user_intent") or ""
        )
        grid = TICKER_GRID[ticker]

        def j(values: list[Any]) -> str:
            return json.dumps(values, ensure_ascii=False)

        rows.append(
            {
                "question": question or proposal["question"],
                "expected_header_paths": j([loc.header_path for loc in locations]),
                "expected_tickers": j([ticker]),
                "match_mode": "startswith",
                "answer_snippets": j([loc.snippet for loc in locations]),
                "query_type": QUERY_TYPE_OVERRIDES.get(
                    candidate_id, proposal["query_type"]
                ),
                "answer_spans": j([loc.span for loc in locations]),
                "block_heading": j([loc.block_heading for loc in locations]),
                "detection_source": j([loc.detection_source for loc in locations]),
                "sector": grid["sector"],
                "market_cap_bucket": grid["cap"],
                "generation_mode": review_row["generation_mode"],
                "user_intent": intent,
                "curation_note": proposal.get("reason", ""),
                "generated_by": ROUND2_GENERATOR if is_new else ROUND1_GENERATOR,
                "fiscal_year": str(candidate["_fiscal_year"]),
                "accession_number": candidate["_accession"],
                "candidate_id": candidate_id,
                "answer_requirement": requirement or review_row["answer_requirement"],
                "review_provenance": _provenance(candidate_id, dropped),
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DATASET_PATH)
    args = parser.parse_args(argv)

    filings = load_filings()
    rows = build_rows(filings)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DATASET_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    issues = validate_rows(load_csv_rows(args.out), filings)
    for issue in issues:
        print(f"[{issue.row_id}] {issue.rule}: {issue.message}")
    print(f"{'FAIL' if issues else 'OK'} — {len(rows)} rows written to {args.out}")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
