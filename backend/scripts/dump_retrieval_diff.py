#!/usr/bin/env python
"""Qualitative retrieval diff dump for the RAG filter article.

Picks a handful of queries from the experiment dataset and dumps top-5
side-by-side from the naive vs three-layer collections into a markdown
file. Output is the raw material for the article's "before/after" tables.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from backend.evals.eval_tasks import (  # noqa: E402
    NAIVE_COLLECTION,
    _eval_search,
)

DEFAULT_DATASET = (
    Path(__file__).resolve().parents[1]
    / "evals"
    / "scenarios"
    / "rag_filter_three_layer"
    / "dataset.csv"
)

# Curated highlight queries — pick the ones that best demonstrate the
# entity-mismatch story (low naive precision + clear cross-ticker bleed).
HIGHLIGHT_QUESTIONS = [
    "AMD 面臨的供應鏈與製程依賴風險?",
    "Google 最新財報提到哪些供應鏈風險?",
    "輝達面臨哪些客戶集中度風險?",
    "AMD 的 AI 加速器產品有什麼策略?",
    "蘋果硬體產品的供應鏈集中度問題?",
]


def _truncate(s: str, n: int) -> str:
    s = " ".join(s.split())  # collapse whitespace
    return s if len(s) <= n else s[: n - 1] + "…"


def _render_top5_table(chunks: list[dict], target_ticker: str) -> str:
    lines = [
        "| Rank | Match | Ticker | Item | Score | Snippet (前 ~120 字) |",
        "|------|-------|--------|------|-------|----------------------|",
    ]
    for i, c in enumerate(chunks[:5], 1):
        ticker = c.get("ticker", "?")
        marker = "✓" if ticker == target_ticker else "✗"
        item = c.get("item", "")
        score = c.get("score", 0.0)
        snippet = _truncate(c.get("text", ""), 120)
        lines.append(
            f"| {i} | {marker} | {ticker} | {item} | {score:.4f} | {snippet} |"
        )
    return "\n".join(lines)


async def _dump_one(
    question: str,
    target_ticker: str,
    target_entity_zh: str,
    three_layer_collection: str,
) -> str:
    naive = await _eval_search(
        collection=NAIVE_COLLECTION,
        query=question,
        ticker_filter=None,
        top_k=5,
    )
    filtered = await _eval_search(
        collection=three_layer_collection,
        query=question,
        ticker_filter=target_ticker,
        top_k=5,
    )

    parts = [
        f"## Query: {question}",
        f"**Target**: `{target_ticker}` ({target_entity_zh})",
        "",
        "### Naive collection (no filter, no payload index, no tenant)",
        _render_top5_table(naive["retrieved_chunks"], target_ticker),
        "",
        "### Three-layer collection (filter ticker, tenant-aware HNSW)",
        _render_top5_table(filtered["retrieved_chunks"], target_ticker),
        "",
    ]
    return "\n".join(parts)


def _read_dataset(dataset_path: Path) -> list[dict[str, str]]:
    with dataset_path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


async def _amain(args: argparse.Namespace) -> int:
    import os

    dataset_rows = _read_dataset(args.dataset)
    by_question = {r["question"]: r for r in dataset_rows}

    selected = []
    for q in HIGHLIGHT_QUESTIONS:
        if q not in by_question:
            print(f"Skipping (not in dataset): {q}", file=sys.stderr)
            continue
        selected.append(by_question[q])

    three_layer = os.environ.get(
        "SEC_QDRANT_COLLECTION", "sec_filings_openai_large_dense_baseline"
    )

    sections = [
        "# Retrieval Diff — Naive vs Three-layer",
        "",
        f"_Generated {datetime.now(tz=timezone.utc).isoformat()}_",
        "",
        f"- Naive collection: `{NAIVE_COLLECTION}` "
        "(no payload index, no `is_tenant`, query without filter)",
        f"- Three-layer collection: `{three_layer}` "
        "(`is_tenant=True` on ticker, query with `must=[ticker=X]`)",
        "",
        "Both collections share identical embeddings — naive was populated "
        "via Qdrant scroll + upsert from the three-layer collection. Only "
        "build-time payload-index config and query-time filter differ.",
        "",
        "---",
        "",
    ]
    for row in selected:
        section = await _dump_one(
            question=row["question"],
            target_ticker=row["target_ticker"],
            target_entity_zh=row["target_entity_zh"],
            three_layer_collection=three_layer,
        )
        sections.append(section)
        sections.append("---")
        sections.append("")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = args.output_dir / f"retrieval_diff_{ts}.md"
    out_path.write_text("\n".join(sections), encoding="utf-8")
    print(out_path)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "artifacts",
    )
    args = parser.parse_args(argv)
    return asyncio.run(_amain(args))


if __name__ == "__main__":
    sys.exit(main())
