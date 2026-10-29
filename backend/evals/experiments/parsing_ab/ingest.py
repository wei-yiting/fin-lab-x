"""Ingest every dataset (ticker, fiscal year) into both A/B collections.

Each arm runs its production ingest path, unmodified, into its own
collection (see :mod:`.arms`):

- ``text``: the filing-store ``ParsedFiling`` the dataset was validated
  against (ADR-0016), Item 8 dropped, through
  ``sec_dense_pipeline.vectorizer.ingest_filing_with_retry``.
- ``html``: ``SECFilingPipeline.process`` (EDGAR download + frozen HTML parse,
  cached under ``data/sec_filings_html/``) through
  ``sec_dense_pipeline_html.vectorizer.ingest_filing``. Item 8 stays in the
  collection; the run excludes it at query time.

Writes ``ingest_manifest.json``: per (ticker, arm) chunk counts, the item
label distribution, both arms' accession numbers (they must be the same
filing), and any failure. A failure is recorded and the batch continues.

Usage::

    python -m backend.evals.experiments.parsing_ab.ingest \\
        --dataset <dataset.csv> --out <ingest_manifest.json> [--only TICKER ...]
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from collections import Counter
from importlib.metadata import version
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

from qdrant_client import QdrantClient, models  # noqa: E402

from backend.common.data_paths import get_sec_text_dir  # noqa: E402
from backend.common.sec_core import FilingType  # noqa: E402
from backend.evals.experiments.parsing_ab.analyze import (  # noqa: E402
    load_dataset,
    ticker_for,
)
from backend.evals.experiments.parsing_ab.arms import (  # noqa: E402
    HTML_COLLECTION,
    TEXT_COLLECTION,
    configure_environment,
    drop_excluded_items,
    embedding_config,
)
from backend.ingestion.sec_dense_pipeline import vectorizer as text_vectorizer  # noqa: E402
from backend.ingestion.sec_dense_pipeline.chunking import (  # noqa: E402
    CHUNK_OVERLAP_TOKENS,
    CHUNK_SIZE_TOKENS,
)
from backend.ingestion.sec_dense_pipeline_html import (  # noqa: E402
    vectorizer as html_vectorizer,
)
from backend.ingestion.sec_filing_pipeline_html.pipeline import (  # noqa: E402
    SECFilingPipeline,
)
from backend.ingestion.sec_text_pipeline.filing_store import LocalFilingStore  # noqa: E402

_MARKER_STATUSES = ["pending", "complete"]


def dataset_filings(rows: list[dict[str, str]]) -> list[tuple[str, int]]:
    return sorted({(ticker_for(r), int(r["fiscal_year"])) for r in rows})


def _item_counts(
    client: QdrantClient, collection: str, ticker: str, year_key: str, year: int
) -> Counter[str]:
    counts: Counter[str] = Counter()
    offset = None
    scroll_filter = models.Filter(
        must=[
            models.FieldCondition(key="ticker", match=models.MatchValue(value=ticker)),
            models.FieldCondition(key=year_key, match=models.MatchValue(value=year)),
        ],
        must_not=[
            models.FieldCondition(
                key="status", match=models.MatchAny(any=_MARKER_STATUSES)
            )
        ],
    )
    while True:
        points, offset = client.scroll(
            collection_name=collection,
            scroll_filter=scroll_filter,
            limit=256,
            offset=offset,
            with_payload=["item"],
            with_vectors=False,
        )
        counts.update(str((p.payload or {}).get("item")) for p in points)
        if offset is None:
            return counts


def ingest_text(ticker: str, fiscal_year: int) -> dict[str, Any]:
    store_path = get_sec_text_dir() / ticker / "10-K" / f"{fiscal_year}.json"
    filing = LocalFilingStore().get(ticker, FilingType.TEN_K, fiscal_year)
    if filing is None:
        raise FileNotFoundError(f"no filing-store entry at {store_path}")
    filtered, dropped = drop_excluded_items(filing)
    asyncio.run(text_vectorizer.ingest_filing_with_retry(filtered))
    return {
        "accession_number": filing.metadata.accession_number,
        "store_sha256": hashlib.sha256(store_path.read_bytes()).hexdigest(),
        "items_dropped": dropped,
    }


def ingest_html(
    pipeline: SECFilingPipeline, ticker: str, fiscal_year: int
) -> dict[str, Any]:
    filing = pipeline.process(ticker, "10-K", fiscal_year)
    asyncio.run(
        html_vectorizer.ingest_filing(
            ticker=ticker,
            year=filing.metadata.fiscal_year,
            markdown=filing.markdown_content,
            filing_metadata=filing.metadata,
        )
    )
    return {
        "accession_number": filing.metadata.accession_number,
        "fiscal_year": filing.metadata.fiscal_year,
        "markdown_chars": len(filing.markdown_content),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest both parsing A/B arms")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", nargs="*", default=None, help="Ticker subset")
    parser.add_argument(
        "--arms", nargs="+", choices=["text", "html"], default=["text", "html"]
    )
    args = parser.parse_args(argv)

    configure_environment()
    filings = dataset_filings(load_dataset(args.dataset))
    if args.only:
        wanted = {t.upper() for t in args.only}
        filings = [f for f in filings if f[0] in wanted]

    manifest: dict[str, Any] = (
        json.loads(args.out.read_text(encoding="utf-8")) if args.out.exists() else {}
    )
    manifest["collections"] = {"html": HTML_COLLECTION, "text": TEXT_COLLECTION}
    manifest["embedding"] = embedding_config()
    manifest.setdefault("edgartools", {}).update(
        {arm: version("edgartools") for arm in args.arms}
    )
    manifest["chunking"] = {
        "html": {
            "size_tokens": int(os.environ.get("SEC_CHUNK_SIZE", "512")),
            "overlap_tokens": int(os.environ.get("SEC_CHUNK_OVERLAP", "50")),
        },
        "text": {
            "size_tokens": CHUNK_SIZE_TOKENS,
            "overlap_tokens": CHUNK_OVERLAP_TOKENS,
        },
    }
    filings_out: dict[str, Any] = manifest.setdefault("filings", {})

    pipeline = SECFilingPipeline.create()
    client = QdrantClient(url="http://localhost:6333")
    for ticker, fiscal_year in filings:
        key = f"{ticker}/{fiscal_year}"
        entry: dict[str, Any] = dict(filings_out.get(key, {}))
        for arm in args.arms:
            try:
                info = (
                    ingest_text(ticker, fiscal_year)
                    if arm == "text"
                    else ingest_html(pipeline, ticker, fiscal_year)
                )
                collection = TEXT_COLLECTION if arm == "text" else HTML_COLLECTION
                year_key = "fiscal_year" if arm == "text" else "year"
                items = _item_counts(client, collection, ticker, year_key, fiscal_year)
                info["chunks"] = sum(items.values())
                info["items"] = dict(sorted(items.items()))
                info["status"] = "ok"
            except Exception as exc:  # noqa: BLE001 — record and continue the batch
                info = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
            entry[arm] = info
            print(
                f"{key:<12} {arm:<5} {info['status']:<7} "
                f"{info.get('chunks', '')} {info.get('error', '')}",
                flush=True,
            )
        if entry["text"].get("accession_number") and entry["html"].get(
            "accession_number"
        ):
            entry["same_accession"] = (
                entry["text"]["accession_number"] == entry["html"]["accession_number"]
            )
        filings_out[key] = entry
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    failed = [
        k
        for k, e in filings_out.items()
        if any(e[a]["status"] != "ok" for a in ("text", "html"))
        or not e.get("same_accession", False)
    ]
    print(f"\n{len(filings_out)} filings, problems: {failed or 'none'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
