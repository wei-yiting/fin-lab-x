"""Qdrant collection + payload-index lifecycle for the SEC dense pipeline.

New-contract collection: payload indexes on ``ticker`` (tenant),
``fiscal_year``, and ``item``. Race-safe against concurrent workers creating
the same collection or index.

Unlike the frozen ``_html`` baseline's version, there is no schema
reconciliation step: this collection is born with the tenant ticker index, so
no legacy non-tenant index can exist that would need migrating. Ensuring is
therefore a plain idempotent create-if-missing over the full index set.
"""

from __future__ import annotations

from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

_TICKER_INDEX_SCHEMA = models.KeywordIndexParams(
    type=models.KeywordIndexType.KEYWORD,
    is_tenant=True,
)

_INDEXES: tuple[
    tuple[str, models.KeywordIndexParams | models.PayloadSchemaType], ...
] = (
    ("ticker", _TICKER_INDEX_SCHEMA),
    ("fiscal_year", models.PayloadSchemaType.INTEGER),
    ("item", models.PayloadSchemaType.KEYWORD),
)


def _is_already_exists_error(exc: BaseException) -> bool:
    """Detect Qdrant's already-exists response from a concurrent create.

    Qdrant returns 400 with an 'already exists' message; the exact wording has
    varied across server versions, so we match on status_code + message body.
    """
    if not isinstance(exc, UnexpectedResponse):
        return False
    status = getattr(exc, "status_code", None)
    if status not in (400, 409):
        return False
    body = getattr(exc, "content", b"") or b""
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    text = f"{body} {exc}".lower()
    return "already exists" in text or "already has" in text


async def async_ensure_collection_and_indexes(
    client: AsyncQdrantClient, collection: str, vector_size: int
) -> None:
    """Create the collection if missing and ensure all payload indexes exist."""
    if not await client.collection_exists(collection):
        try:
            await client.create_collection(
                collection_name=collection,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE,
                ),
            )
        except UnexpectedResponse as exc:
            # Another worker won the create race; the index set below is
            # idempotent either way.
            if not _is_already_exists_error(exc):
                raise
    for field, schema in _INDEXES:
        try:
            await client.create_payload_index(
                collection_name=collection,
                field_name=field,
                field_schema=schema,
            )
        except UnexpectedResponse as exc:
            if not _is_already_exists_error(exc):
                raise
