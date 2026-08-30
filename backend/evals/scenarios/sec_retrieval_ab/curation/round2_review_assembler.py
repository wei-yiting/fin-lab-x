"""Assemble the second human-review surface from per-ticker curation results."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

REVIEW_COLUMNS = [
    "review_scope",
    "ticker",
    "fiscal_year",
    "items",
    "generation_mode",
    "round1_query_type",
    "round1_question",
    "round1_snippet_preview",
    "round1_decision",
    "round1_reviewer_comment",
    "round2_query_type",
    "round2_question",
    "answer_requirement",
    "curation_note",
    "change_summary",
    "acceptable_occurrence_count",
    "round2_snippet_previews",
    "candidate_id",
    "round2_decision",
    "round2_reviewer_comment",
]

_FALLBACK_REQUIREMENTS = {
    "p16": "One independently sufficient occurrence must identify the material, labor, and overhead cost components Linde includes when accounting for equipment contracts.",
    "p18": "One independently sufficient occurrence must state how export-authorization requirements can restrict or eliminate Datadog sales opportunities.",
    "p20": "One independently sufficient occurrence must identify EOFlow's appeal and uncertain ability to satisfy the damages award as threats to collection.",
    "p23": "One independently sufficient occurrence must state the fiscal 2026 percentage increase and resulting total unit volume for Deckers.",
    "p25": "One independently sufficient occurrence must state the relative tariff impact if Caterpillar does not take its planned 2026 mitigation actions; an inferred dollar amount is not acceptable.",
    "p28": "One independently sufficient occurrence must quantify how a change in the nuclear-decommissioning cost-escalation assumption would affect NEE's retirement obligations.",
    "p30": "One independently sufficient occurrence must state where Linde's 2025 capital expenditures were concentrated geographically.",
    "p31": "One independently sufficient occurrence must connect ExxonMobil's career-oriented talent-development approach to employee retention or tenure.",
    "p32": "One independently sufficient occurrence must state the size of ExxonMobil's active patent portfolio at the end of 2025.",
    "p34": "One independently sufficient occurrence must explain how Datadog Database Monitoring identifies database bottlenecks.",
    "p38": "One independently sufficient occurrence must explain what happens to ownership of underlying staked Ether when cbETH is sold or transferred.",
    "p40": "One independently sufficient occurrence must identify the cybersecurity policies or procedures Deckers periodically reviews and updates.",
    "p41": "One independently sufficient occurrence must identify who independently tests Alphabet's cybersecurity controls.",
    "p42": "One independently sufficient occurrence must state how frequently Caterpillar's CIO attends Audit Committee meetings.",
    "p50": "One independently sufficient occurrence must identify the types of confidential, proprietary, or personal information that Linde security failures or breaches could expose.",
    "a18": "One independently sufficient occurrence must state Datadog's trailing 12-month dollar-based net-retention rates for both 2024 and 2025.",
    "a23": "One independently sufficient occurrence must state Deckers' constant-currency net-sales increase in fiscal 2026.",
}


def _read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_results(curation_dir: Path) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for path in sorted((curation_dir / "round2_ticker_results").glob("T*.json")):
        ticker_result = _read_json(path)
        for candidate in ticker_result["candidate_results"]:
            candidate_id = candidate["candidate_id"]
            if candidate_id in results:
                raise ValueError(f"duplicate candidate result: {candidate_id}")
            candidate["_ticker"] = ticker_result["ticker"]
            candidate["_fiscal_year"] = ticker_result["fiscal_year"]
            candidate["_accession_number"] = ticker_result["source"]["accession_number"]
            results[candidate_id] = candidate
    if len(results) != 51:
        raise ValueError(f"expected 51 active results, found {len(results)}")
    return results


def _load_new_questions(curation_dir: Path) -> dict[str, dict[str, str]]:
    return {
        row["candidate_id"]: row
        for row in _read_csv(curation_dir / "round2_intent_first_questions.csv")
    }


def _item_labels(candidate: dict[str, Any]) -> str:
    labels: list[str] = []
    for occurrence in candidate["acceptable_occurrences"]:
        anchor = occurrence.get("store_anchor") or {}
        raw = str(anchor.get("item") or occurrence.get("item_hint") or "").strip()
        if not raw:
            continue
        label = raw if raw.lower().startswith("item ") else f"Item {raw.upper()}"
        if label not in labels:
            labels.append(label)
    if not labels:
        for raw in candidate["proposal"].get("item_keys", []):
            label = f"Item {str(raw).upper()}"
            if label not in labels:
                labels.append(label)
    return " | ".join(labels)


def _answer_requirement(candidate: dict[str, Any]) -> str:
    proposal = candidate["proposal"]
    explicit = proposal.get("answer_requirement")
    if explicit:
        return str(explicit)
    candidate_id = candidate["candidate_id"]
    if candidate_id in _FALLBACK_REQUIREMENTS:
        return _FALLBACK_REQUIREMENTS[candidate_id]
    raise ValueError(f"missing answer requirement for {candidate_id}")


def _generation_mode(
    candidate_id: str,
    round1_row: dict[str, str] | None,
    new_questions: dict[str, dict[str, str]],
) -> str:
    if round1_row is not None:
        return round1_row["generation_mode"]
    return new_questions[candidate_id]["generation_mode"]


def _curation_note(
    candidate: dict[str, Any],
    original_candidates: dict[str, dict[str, Any]],
    new_questions: dict[str, dict[str, str]],
) -> str:
    candidate_id = candidate["candidate_id"]
    if candidate_id in original_candidates:
        return str(original_candidates[candidate_id]["curation_note"])
    proposal = candidate["proposal"]
    return str(
        proposal.get("investor_intent")
        or new_questions[candidate_id].get("investor_intent")
        or proposal["reason"]
    )


def _snippet_previews(candidate: dict[str, Any]) -> str:
    previews = []
    for occurrence in candidate["acceptable_occurrences"]:
        anchor = occurrence.get("store_anchor") or {}
        previews.append(
            {
                "occurrence_id": occurrence["occurrence_id"],
                "item": anchor.get("item") or occurrence.get("item_hint", ""),
                "location": occurrence.get("filing_location", ""),
                "snippet": occurrence["answer_snippet"],
            }
        )
    return json.dumps(previews, ensure_ascii=False)


def build_review_rows(curation_dir: Path) -> list[dict[str, str]]:
    """Build ordered, one-candidate-per-row records for human review."""
    round1_rows = _read_csv(curation_dir / "review.csv")
    round1_by_id = {row["candidate_id"]: row for row in round1_rows}
    round1_order = {row["candidate_id"]: index for index, row in enumerate(round1_rows)}
    original_candidates = {
        candidate["candidate_id"]: candidate
        for candidate in _read_json(curation_dir / "candidates.json")
    }
    new_questions = _load_new_questions(curation_dir)
    results = _load_results(curation_dir)

    active_old = [
        candidate
        for candidate in results.values()
        if candidate["candidate_id"] in round1_by_id
    ]
    decision_rank = {"o": 0, "?": 1}
    active_old.sort(
        key=lambda candidate: (
            decision_rank[round1_by_id[candidate["candidate_id"]]["approved"]],
            round1_order[candidate["candidate_id"]],
        )
    )
    active_new = sorted(
        (
            candidate
            for candidate in results.values()
            if candidate["candidate_id"] not in round1_by_id
        ),
        key=lambda candidate: candidate["candidate_id"],
    )
    reference_rows = [
        row
        for row in round1_rows
        if row["query_type"] != "multi_passage" and row["approved"] in {"!", "x"}
    ]
    reference_rows.sort(
        key=lambda row: (
            {"!": 0, "x": 1}[row["approved"]],
            round1_order[row["candidate_id"]],
        )
    )

    rows: list[dict[str, str]] = []
    for candidate in [*active_old, *active_new]:
        candidate_id = candidate["candidate_id"]
        round1 = round1_by_id.get(candidate_id)
        proposal = candidate["proposal"]
        rows.append(
            {
                "review_scope": "active" if round1 is not None else "active_new",
                "ticker": candidate["_ticker"],
                "fiscal_year": str(candidate["_fiscal_year"]),
                "items": _item_labels(candidate),
                "generation_mode": _generation_mode(
                    candidate_id, round1, new_questions
                ),
                "round1_query_type": round1["query_type"] if round1 else "",
                "round1_question": round1["question"] if round1 else "",
                "round1_snippet_preview": (round1["snippet_preview"] if round1 else ""),
                "round1_decision": round1["approved"] if round1 else "",
                "round1_reviewer_comment": (
                    round1["reviewer_comment"] if round1 else ""
                ),
                "round2_query_type": proposal["query_type"],
                "round2_question": proposal["question"],
                "answer_requirement": _answer_requirement(candidate),
                "curation_note": _curation_note(
                    candidate, original_candidates, new_questions
                ),
                "change_summary": proposal["reason"],
                "acceptable_occurrence_count": str(
                    len(candidate["acceptable_occurrences"])
                ),
                "round2_snippet_previews": _snippet_previews(candidate),
                "candidate_id": candidate_id,
                "round2_decision": "",
                "round2_reviewer_comment": "",
            }
        )

    for round1 in reference_rows:
        original = original_candidates[round1["candidate_id"]]
        rows.append(
            {
                "review_scope": "reference_only",
                "ticker": round1["ticker"],
                "fiscal_year": str(original["fiscal_year"]),
                "items": " | ".join(
                    f"Item {str(item).upper()}"
                    for item in original["plan"]["item_keys"]
                ),
                "generation_mode": round1["generation_mode"],
                "round1_query_type": round1["query_type"],
                "round1_question": round1["question"],
                "round1_snippet_preview": round1["snippet_preview"],
                "round1_decision": round1["approved"],
                "round1_reviewer_comment": round1["reviewer_comment"],
                "round2_query_type": "",
                "round2_question": "",
                "answer_requirement": "",
                "curation_note": original["curation_note"],
                "change_summary": "Not carried into the 51-candidate active pool.",
                "acceptable_occurrence_count": "0",
                "round2_snippet_previews": "[]",
                "candidate_id": round1["candidate_id"],
                "round2_decision": "",
                "round2_reviewer_comment": "",
            }
        )
    return rows


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>") or "—"


def _blockquote(text: str) -> str:
    lines = (line.rstrip(" \t") for line in text.splitlines())
    return "\n".join(f"> {line}" if line else ">" for line in lines)


def _span_with_bold_snippet(span: str, snippet: str) -> str:
    index = span.find(snippet)
    if index < 0:
        return f"{_blockquote(span)}\n\nSnippet: **{snippet}**"
    marked = f"{span[:index]}**{snippet}**{span[index + len(snippet) :]}"
    return _blockquote(marked)


def _reconciliation_reasons(candidate: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for task, details in (candidate.get("round3_reconciliation") or {}).items():
        entries = details if isinstance(details, list) else [details]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            reason = entry.get("reason")
            if reason:
                reasons.append(f"{task.upper()}: {reason}")
            for removal in entry.get("removed_occurrences", []):
                if removal.get("reason"):
                    reasons.append(f"{task.upper()} removal: {removal['reason']}")
    return reasons


def _render_markdown(curation_dir: Path, rows: list[dict[str, str]]) -> str:
    results = _load_results(curation_dir)
    original_candidates = {
        candidate["candidate_id"]: candidate
        for candidate in _read_json(curation_dir / "candidates.json")
    }
    lines = [
        "# sec_retrieval_ab dataset — Round 2 human review",
        "",
        "This surface contains 51 active candidates and 4 reference-only Round-1 rows. Fill only `round2_decision` and `round2_reviewer_comment` in `round2_review.csv`; both fields are intentionally blank.",
        "",
        "Every listed Round-2 evidence occurrence is an **OR alternative**: retrieving any one occurrence counts as a hit, and every occurrence must independently satisfy the answer requirement.",
        "",
        "## Review order",
        "",
        "| group | rows | review expectation |",
        "|---|---:|---|",
        "| Round-1 `o` | 13 | Re-review the current question and complete OR-set |",
        "| Round-1 `?` | 28 | Compare the correction with the original issue |",
        "| New `n01`–`n10` | 10 | First human review |",
        "| Round-1 `!` / `x` | 4 | Reference only; excluded from active pool |",
        "",
    ]

    for row in rows:
        candidate_id = row["candidate_id"]
        candidate = results.get(candidate_id)
        original = original_candidates.get(candidate_id)
        lines.extend(
            [
                f"## Candidate {candidate_id} — {row['ticker']}",
                "",
                f"- Scope: `{row['review_scope']}`",
                f"- FY: `{row['fiscal_year']}`",
                f"- Items: {row['items'] or '—'}",
                f"- Generation mode: `{row['generation_mode']}`",
                "",
                "### Round-1 review",
                "",
                f"- Decision: `{row['round1_decision']}`"
                if row["round1_decision"]
                else "- Decision: — (new candidate)",
                f"- Round-1 reviewer comment: {row['round1_reviewer_comment'] or '—'}",
                "",
                "| field | Round 1 | Round 2 |",
                "|---|---|---|",
                f"| Question | {_escape_table(row['round1_question'])} | {_escape_table(row['round2_question'])} |",
                f"| Query type | {_escape_table(row['round1_query_type'])} | {_escape_table(row['round2_query_type'])} |",
                f"| Evidence occurrences | {len(original['evidences']) if original else 0} | {row['acceptable_occurrence_count']} |",
                "",
            ]
        )

        if original is not None:
            lines.extend(["#### Round-1 evidence", ""])
            for index, evidence in enumerate(original["evidences"], start=1):
                lines.extend(
                    [
                        f"**Original evidence {index}** — `{evidence['header_path']}`",
                        "",
                        _span_with_bold_snippet(evidence["span"], evidence["snippet"]),
                        "",
                    ]
                )

        if candidate is None:
            lines.extend(
                [
                    "### Round-2 disposition",
                    "",
                    "This row is reference-only and was not carried into the 51-candidate active pool.",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "### Round-2 proposal",
                    "",
                    f"- Answer requirement: {row['answer_requirement']}",
                    f"- Curation note: {row['curation_note']}",
                    f"- Change summary: {row['change_summary']}",
                    "",
                    "#### Acceptable OR alternatives",
                    "",
                ]
            )
            for index, occurrence in enumerate(
                candidate["acceptable_occurrences"], start=1
            ):
                anchor = occurrence.get("store_anchor") or {}
                item = anchor.get("item") or occurrence.get("item_hint") or "unknown"
                lines.extend(
                    [
                        f"**OR alternative {index}** — `{occurrence['occurrence_id']}`",
                        "",
                        f"- Store Item: `{item}`",
                        f"- Location: {occurrence.get('filing_location', '—')}",
                        f"- Acceptance reason: {occurrence.get('acceptance_reason', '—')}",
                        "",
                        _span_with_bold_snippet(
                            occurrence["answer_span"], occurrence["answer_snippet"]
                        ),
                        "",
                    ]
                )
            reasons = _reconciliation_reasons(candidate)
            if reasons:
                lines.extend(["#### Evidence provenance", ""])
                lines.extend(f"- {reason}" for reason in reasons)
                lines.append("")

        lines.extend(
            [
                "### Human review — Round 2",
                "",
                "- `round2_decision`: _(blank)_",
                "- `round2_reviewer_comment`: _(blank)_",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(lines)


def assemble_review_artifacts(
    curation_dir: Path, csv_path: Path, markdown_path: Path
) -> None:
    """Write the ordered CSV and expanded Markdown human-review artifacts."""
    rows = build_review_rows(curation_dir)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=REVIEW_COLUMNS,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(
            {
                key: "\n".join(
                    line.rstrip(" \t")
                    for line in value.replace("\r\n", "\n")
                    .replace("\r", "\n")
                    .split("\n")
                )
                if isinstance(value, str)
                else value
                for key, value in row.items()
            }
            for row in rows
        )
    markdown_path.write_text(_render_markdown(curation_dir, rows), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--curation-dir", type=Path, default=Path(__file__).resolve().parent
    )
    args = parser.parse_args()
    curation_dir = args.curation_dir
    assemble_review_artifacts(
        curation_dir,
        curation_dir / "round2_review.csv",
        curation_dir / "round2_review.md",
    )


if __name__ == "__main__":
    main()
