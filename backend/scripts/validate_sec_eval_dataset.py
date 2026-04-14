#!/usr/bin/env python
"""Validate SEC retrieval eval dataset against live Qdrant.

Checks that expected_header_paths entries have matching chunks in Qdrant,
and reports near-miss warnings for case mismatches.

Usage: python -m backend.scripts.validate_sec_eval_dataset [--csv path]
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

from qdrant_client import QdrantClient


def _parse_json_field(value: str) -> list[str] | None:
    """Parse a JSON list from a CSV field. Returns None on parse failure."""
    if not value or value.strip() == "[]":
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        return None
    return None


def validate_dataset(
    csv_path: Path,
    qdrant_url: str,
    collection: str,
) -> int:
    """Validate dataset rows against Qdrant. Returns exit code."""
    client = QdrantClient(url=qdrant_url)

    if not client.collection_exists(collection):
        print(f"ERROR: Collection '{collection}' does not exist.")
        return 1

    all_points = []
    offset = None
    while True:
        batch, offset = client.scroll(
            collection_name=collection,
            limit=1000,
            offset=offset,
            with_payload=True,
        )
        all_points.extend(batch)
        if offset is None:
            break
    content_points = [p for p in all_points if p.payload.get("status") is None]

    if not content_points:
        print(f"ERROR: Collection '{collection}' has 0 content points.")
        return 1

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    has_failures = False
    for row_idx, row in enumerate(rows, start=1):
        expected_paths = _parse_json_field(
            row.get("expected_header_paths", "")
        )
        answer_snippets = _parse_json_field(
            row.get("answer_snippets", "")
        )

        if expected_paths is None:
            print(f"  Row {row_idx}: ERROR malformed expected_header_paths JSON")
            has_failures = True
            continue
        if answer_snippets is None:
            print(f"  Row {row_idx}: ERROR malformed answer_snippets JSON")
            has_failures = True
            continue

        if not expected_paths:
            print(f"  Row {row_idx}: SKIP (no expected_header_paths)")
            continue

        row_pass = True
        for path_idx, expected_path in enumerate(expected_paths):
            exact_matches = [
                p
                for p in content_points
                if p.payload.get("header_path", "").startswith(expected_path)
            ]

            if exact_matches:
                # Check snippet if provided
                snippet = (
                    answer_snippets[path_idx]
                    if path_idx < len(answer_snippets)
                    else None
                )
                if snippet:
                    snippet_matches = [
                        p
                        for p in exact_matches
                        if snippet.lower()
                        in p.payload.get("text", "").lower()
                    ]
                    if not snippet_matches:
                        print(
                            f"  Row {row_idx}: WARN path='{expected_path}' "
                            f"matched {len(exact_matches)} chunks but "
                            f"snippet '{snippet}' not found in any"
                        )
                else:
                    print(
                        f"  Row {row_idx}: OK path='{expected_path}' "
                        f"({len(exact_matches)} matches)"
                    )
                continue

            # No exact match — check for case-insensitive near-miss
            case_insensitive_matches = [
                p
                for p in content_points
                if p.payload.get("header_path", "")
                .lower()
                .startswith(expected_path.lower())
            ]

            if case_insensitive_matches:
                actual_paths = {
                    p.payload.get("header_path", "")
                    for p in case_insensitive_matches
                }
                print(
                    f"  Row {row_idx}: NEAR-MISS path='{expected_path}' "
                    f"— case-insensitive match found. "
                    f"Actual: {list(actual_paths)[:3]}"
                )
                row_pass = False
                has_failures = True
            else:
                print(
                    f"  Row {row_idx}: FAIL path='{expected_path}' "
                    f"— no matching chunks found"
                )
                row_pass = False
                has_failures = True

        if row_pass:
            pass  # Already printed per-path status

    return 1 if has_failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate SEC retrieval eval dataset"
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("backend/evals/scenarios/sec_retrieval/dataset.csv"),
        help="Path to dataset CSV",
    )
    args = parser.parse_args(argv)

    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    collection = os.environ.get(
        "SEC_QDRANT_COLLECTION",
        "sec_filings_openai_large_dense_baseline",
    )

    if not args.csv.is_file():
        print(f"ERROR: CSV file not found: {args.csv}")
        return 1

    print(f"Validating {args.csv} against {collection}...")
    return validate_dataset(args.csv, qdrant_url, collection)


if __name__ == "__main__":
    sys.exit(main())
