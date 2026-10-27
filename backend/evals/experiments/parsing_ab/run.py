"""Run every dataset row against both A/B arms and record raw retrievals.

Preflight first: every (ticker, fiscal year) the dataset touches must have a
``complete`` commit marker in both collections, otherwise the run refuses to
start (a missing filing must surface as a coverage gap, never as a silent JIT
ingest or a retrieval miss). Then each row is sent to both arms with the same
question, the same (ticker, fiscal year) scope, ``top_k`` and query vector.

Writes one JSON line per (row, arm) to ``retrievals.jsonl`` plus
``run_meta.json`` (revision, dataset hash, collections, point counts).

Usage::

    python -m backend.evals.experiments.parsing_ab.run \\
        --dataset <dataset.csv> --out-dir <dir>
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

from qdrant_client import QdrantClient, models  # noqa: E402

from backend.evals.experiments.parsing_ab.analyze import (  # noqa: E402
    load_dataset,
    row_id_for,
    ticker_for,
)
from backend.evals.experiments.parsing_ab.arms import (  # noqa: E402
    ARMS,
    HTML_COLLECTION,
    TEXT_COLLECTION,
    TOP_K,
    QueryEmbeddingCache,
    configure_environment,
    embedding_config,
    search_arm,
    shared_query_embeddings,
)
from backend.evals.experiments.parsing_ab.ingest import dataset_filings  # noqa: E402
from backend.ingestion.sec_dense_pipeline import vectorizer as text_vectorizer  # noqa: E402
from backend.ingestion.sec_dense_pipeline.common import (  # noqa: E402
    commit_marker_id as text_marker_id,
)
from backend.ingestion.sec_dense_pipeline_html.common import (  # noqa: E402
    commit_marker_id as html_marker_id,
)

_KEPT_FIELDS = ("header_path", "item", "chunk_index", "score", "text")


def preflight(client: QdrantClient, filings: list[tuple[str, int]]) -> list[str]:
    missing = []
    for arm, collection, marker_id in (
        ("html", HTML_COLLECTION, html_marker_id),
        ("text", TEXT_COLLECTION, text_marker_id),
    ):
        for ticker, fiscal_year in filings:
            points = client.retrieve(
                collection_name=collection, ids=[marker_id(ticker, fiscal_year)]
            )
            if not points or (points[0].payload or {}).get("status") != "complete":
                missing.append(f"{arm}:{ticker}/{fiscal_year}")
    return missing


def _content_points(client: QdrantClient, collection: str) -> int:
    return client.count(
        collection_name=collection,
        count_filter=models.Filter(
            must_not=[
                models.FieldCondition(
                    key="status", match=models.MatchAny(any=["pending", "complete"])
                )
            ]
        ),
    ).count


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout.strip()


async def run_rows(rows: list[dict[str, str]], out: Path) -> None:
    with out.open("w", encoding="utf-8") as f:
        for index, row in enumerate(rows):
            row_id = row_id_for(row, index)
            ticker = ticker_for(row)
            fiscal_year = int(row["fiscal_year"])
            for arm in ARMS:
                record: dict[str, Any] = {
                    "row_id": row_id,
                    "arm": arm,
                    "ticker": ticker,
                    "fiscal_year": fiscal_year,
                    "question": row["question"],
                    "chunks": [],
                    "error": None,
                }
                try:
                    chunks = await search_arm(arm, row["question"], ticker, fiscal_year)
                    record["chunks"] = [
                        {k: c.get(k) for k in _KEPT_FIELDS}
                        | {"ticker": c["ticker"], "year": fiscal_year}
                        for c in chunks
                    ]
                except Exception as exc:  # noqa: BLE001 — recorded per row
                    record["error"] = f"{type(exc).__name__}: {exc}"
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"{row_id} {ticker} done", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run both parsing A/B arms")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    configure_environment()
    rows = load_dataset(args.dataset)
    filings = dataset_filings(rows)
    client = QdrantClient(url="http://localhost:6333")
    missing = preflight(client, filings)
    if missing:
        print(f"preflight failed, not ingested: {missing}", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "started_at": datetime.now(UTC).isoformat(),
        "git_commit": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain")),
        "dataset": str(args.dataset),
        "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "rows": len(rows),
        "filings": [f"{t}/{y}" for t, y in filings],
        "top_k": TOP_K,
        "embedding": embedding_config(),
        "collections": {
            "html": {
                "name": HTML_COLLECTION,
                "content_points": _content_points(client, HTML_COLLECTION),
            },
            "text": {
                "name": TEXT_COLLECTION,
                "content_points": _content_points(client, TEXT_COLLECTION),
            },
        },
    }
    cache = QueryEmbeddingCache(
        args.out_dir / "query_embeddings.json", text_vectorizer._embed_texts
    )
    with shared_query_embeddings(cache):
        asyncio.run(run_rows(rows, args.out_dir / "retrievals.jsonl"))
    meta["finished_at"] = datetime.now(UTC).isoformat()
    (args.out_dir / "run_meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )

    errors = [
        line
        for line in (args.out_dir / "retrievals.jsonl").read_text().splitlines()
        if json.loads(line)["error"]
    ]
    print(f"{len(rows)} rows x {len(ARMS)} arms, errors: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
