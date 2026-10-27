"""The two arms of the HTML-vs-text parsing A/B, behind one interface.

Each arm is its production retrieval path, unmodified, pointed at its own
dedicated Qdrant collection:

- ``html`` — frozen ``sec_filing_pipeline_html`` parse →
  ``sec_dense_pipeline_html`` chunk/embed/``search()``.
- ``text`` — ``sec_text_pipeline`` filing store → ``sec_dense_pipeline``
  chunk/embed/``search()`` (the JIT retriever).

Controlled variables: embedding model and dimension (asserted equal at
import of the run), top-k, the (ticker, fiscal year) scope filter, the Item 8
exclusion, and the query vector itself — both arms' ``_embed_texts`` are
swapped for one shared, disk-persisted cache at query time, so embedding-API
nondeterminism cannot differ between arms. Item 8 is excluded per the
DEV-162 round-3 ruling: the HTML arm by a query-time ``must_not`` on its
``item`` payload (``exclude_items``), the text arm by not ingesting it.
"""

from __future__ import annotations

import json
import os
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from backend.ingestion.sec_dense_pipeline import retriever as text_retriever
from backend.ingestion.sec_dense_pipeline import vectorizer as text_vectorizer
from backend.ingestion.sec_dense_pipeline_html import retriever as html_retriever
from backend.ingestion.sec_dense_pipeline_html import vectorizer as html_vectorizer
from backend.ingestion.sec_text_pipeline.filing_models import ParsedFiling

ARMS = ("html", "text")
TOP_K = 10
HTML_COLLECTION = "sec_ab_parsing_html_20261028"
TEXT_COLLECTION = "sec_ab_parsing_text_20261028"
EXCLUDED_ITEM_KEYS = ("8",)
HTML_EXCLUDED_ITEMS = ["Item 8"]

EmbedFn = Callable[[list[str]], Awaitable[list[list[float]]]]


def configure_environment() -> None:
    """Point both arms at the A/B collections; keep runs off Langfuse."""
    os.environ["SEC_QDRANT_COLLECTION"] = HTML_COLLECTION
    os.environ["SEC_TEXT_QDRANT_COLLECTION"] = TEXT_COLLECTION
    os.environ["LANGFUSE_TRACING_ENABLED"] = "false"
    os.environ.pop("SEC_DISABLE_JIT", None)


def embedding_config() -> dict[str, Any]:
    config = {
        "html": {
            "model": html_vectorizer._EMBED_MODEL,
            "dim": html_vectorizer._EMBED_DIM,
        },
        "text": {
            "model": text_vectorizer._EMBED_MODEL,
            "dim": text_vectorizer._EMBED_DIM,
        },
    }
    if config["html"] != config["text"]:
        raise RuntimeError(f"arms disagree on the embedding model: {config}")
    return config


def drop_excluded_items(filing: ParsedFiling) -> tuple[ParsedFiling, list[str]]:
    """Text arm's Item 8 exclusion: a copy of the filing without those Items."""
    kept = []
    dropped = []
    for item in filing.items:
        key = item.item.strip().lower()
        if key in EXCLUDED_ITEM_KEYS:
            dropped.append(key)
        else:
            kept.append(item)
    return filing.model_copy(update={"items": kept}), dropped


def html_filters(ticker: str, fiscal_year: int) -> dict[str, Any]:
    return {
        "ticker": ticker.strip().upper(),
        "year": fiscal_year,
        "exclude_items": list(HTML_EXCLUDED_ITEMS),
    }


def text_filters(ticker: str, fiscal_year: int) -> dict[str, Any]:
    return {"ticker": ticker.strip().upper(), "fiscal_year": fiscal_year}


class QueryEmbeddingCache:
    """Memoizing, disk-persisted stand-in for both arms' ``_embed_texts``."""

    def __init__(self, path: Path, embed: EmbedFn) -> None:
        self._path = path
        self._embed = embed
        self._vectors: dict[str, list[float]] = (
            json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        )

    async def __call__(self, texts: list[str]) -> list[list[float]]:
        missing = [t for t in dict.fromkeys(texts) if t not in self._vectors]
        if missing:
            for text, vector in zip(missing, await self._embed(missing), strict=True):
                self._vectors[text] = vector
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(self._vectors), encoding="utf-8")
        return [self._vectors[t] for t in texts]


@contextmanager
def shared_query_embeddings(cache: QueryEmbeddingCache) -> Iterator[None]:
    """Route both arms' query embedding through one cache (query time only)."""
    originals = (html_vectorizer._embed_texts, text_vectorizer._embed_texts)
    html_vectorizer._embed_texts = cache  # type: ignore[assignment]
    text_vectorizer._embed_texts = cache  # type: ignore[assignment]
    try:
        yield
    finally:
        html_vectorizer._embed_texts, text_vectorizer._embed_texts = originals


@contextmanager
def _jit_disabled() -> Iterator[None]:
    # Only the text arm can take this flag: the frozen HTML retriever raises
    # on it even for an already-ingested ticker. Run preflight guarantees the
    # HTML arm's commit markers exist, so its JIT path never fires.
    os.environ["SEC_DISABLE_JIT"] = "1"
    try:
        yield
    finally:
        os.environ.pop("SEC_DISABLE_JIT", None)


async def search_arm(
    arm: str, question: str, ticker: str, fiscal_year: int
) -> list[dict[str, Any]]:
    if arm == "html":
        chunks = await html_retriever.search(
            question, filters=html_filters(ticker, fiscal_year), top_k=TOP_K
        )
    elif arm == "text":
        with _jit_disabled():
            chunks = await text_retriever.search(
                question,
                filters=text_filters(ticker, fiscal_year),  # type: ignore[arg-type]
                top_k=TOP_K,
            )
    else:
        raise ValueError(f"unknown arm {arm!r}; expected one of {ARMS}")
    return [chunk.model_dump() for chunk in chunks]
