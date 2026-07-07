#!/usr/bin/env python
"""Build the `sec_filings_naive` Qdrant collection for the A/B experiment.

Copies content points (vectors + payload) from the production three-layer
collection into a sibling collection that has NO payload indexes and NO
tenant configuration. Same embeddings, different HNSW build-time setup.

Skips sentinel markers (payload.status in {pending, complete}) so the naive
collection contains only retrievable content chunks.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from qdrant_client import QdrantClient, models  # noqa: E402

NAIVE_COLLECTION = "sec_filings_naive"
DEFAULT_BATCH = 256


def _content_filter() -> models.Filter:
    return models.Filter(
        must_not=[
            models.FieldCondition(
                key="status",
                match=models.MatchAny(any=["pending", "complete"]),
            ),
        ],
    )


def _create_naive_collection(client: QdrantClient, vector_size: int) -> None:
    """Recreate the naive collection without payload indexes / tenant hints."""
    if client.collection_exists(NAIVE_COLLECTION):
        client.delete_collection(NAIVE_COLLECTION)
    client.create_collection(
        collection_name=NAIVE_COLLECTION,
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=models.Distance.COSINE,
        ),
    )


def _copy_points(
    client: QdrantClient,
    source: str,
    batch: int,
) -> int:
    """Stream content points from source to naive collection. Returns count copied."""
    copied = 0
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=source,
            with_vectors=True,
            with_payload=True,
            limit=batch,
            offset=offset,
            scroll_filter=_content_filter(),
        )
        if not points:
            break

        point_structs: list[models.PointStruct] = []
        for p in points:
            if p.vector is None:
                # Scroll asked for vectors; this should never happen.
                raise RuntimeError(f"Point {p.id} returned without vector")
            point_structs.append(
                models.PointStruct(
                    id=p.id,
                    vector=p.vector,  # pyright: ignore[reportArgumentType]
                    payload=p.payload,
                )
            )
        client.upsert(collection_name=NAIVE_COLLECTION, points=point_structs)
        copied += len(points)
        print(f"  copied {copied} points...", file=sys.stderr)
        if offset is None:
            break

    return copied


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default=os.environ.get(
            "SEC_QDRANT_COLLECTION", "sec_filings_openai_large_dense_baseline"
        ),
        help="Three-layer collection to copy from",
    )
    parser.add_argument("--batch", type=int, default=DEFAULT_BATCH)
    args = parser.parse_args(argv)

    qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
    client = QdrantClient(url=qdrant_url)

    if not client.collection_exists(args.source):
        print(
            f"Source collection '{args.source}' does not exist. "
            "Run backend/scripts/embed_sec_filings.py first.",
            file=sys.stderr,
        )
        return 1

    info = client.get_collection(args.source)
    vector_params = info.config.params.vectors
    if vector_params is None:
        raise RuntimeError(f"Source collection '{args.source}' has no vector config")
    if isinstance(vector_params, dict):
        # Multi-vector config: pick the unnamed default
        vector_params = next(iter(vector_params.values()))
    vector_size = vector_params.size  # pyright: ignore[reportAttributeAccessIssue]

    print(
        f"Source: {args.source}  vector_size={vector_size}",
        file=sys.stderr,
    )
    print(f"Target: {NAIVE_COLLECTION} (will be recreated)", file=sys.stderr)

    _create_naive_collection(client, vector_size=vector_size)
    copied = _copy_points(client, args.source, batch=args.batch)

    naive_count = client.count(collection_name=NAIVE_COLLECTION).count
    source_content_count = client.count(
        collection_name=args.source,
        count_filter=_content_filter(),
    ).count

    print(
        f"\nCopied {copied} points  |  naive total: {naive_count}  |  "
        f"source content: {source_content_count}",
        file=sys.stderr,
    )

    if naive_count != source_content_count:
        print(
            f"MISMATCH: naive ({naive_count}) != source content "
            f"({source_content_count})",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
