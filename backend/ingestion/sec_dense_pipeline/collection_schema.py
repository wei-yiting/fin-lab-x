"""Qdrant collection + payload-index lifecycle for the SEC dense pipeline.

Extracted from vectorizer.py to isolate schema-management concerns (tenant
indexes, race-safe create/reconcile) from the embedding + ingestion logic.
"""

from qdrant_client import models
from qdrant_client.http.exceptions import UnexpectedResponse


_TICKER_INDEX_SCHEMA = models.KeywordIndexParams(
    type=models.KeywordIndexType.KEYWORD,
    is_tenant=True,
)


def _payload_schema(client, collection: str) -> dict:
    """Read existing payload indexes. Only a 404 (missing collection) is
    treated as "no schema"; other errors surface so the caller sees the
    real root cause instead of blindly reissuing CREATE_INDEX calls."""
    try:
        info = client.get_collection(collection)
    except UnexpectedResponse as exc:
        if getattr(exc, "status_code", None) == 404:
            return {}
        raise
    return getattr(info, "payload_schema", {}) or {}


async def _async_payload_schema(client, collection: str) -> dict:
    try:
        info = await client.get_collection(collection)
    except UnexpectedResponse as exc:
        if getattr(exc, "status_code", None) == 404:
            return {}
        raise
    return getattr(info, "payload_schema", {}) or {}


def _is_tenant_index(entry) -> bool:
    params = getattr(entry, "params", None)
    return bool(params and getattr(params, "is_tenant", False))


def _is_already_exists_error(exc: BaseException) -> bool:
    """Detect Qdrant's already-exists response from a concurrent CREATE_INDEX.

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


def ensure_collection_and_indexes(client, collection: str, vector_size: int) -> None:
    """Create the Qdrant collection if missing and ensure all payload indexes
    (ticker as tenant, year, item) are present. Race-safe against concurrent
    workers creating the same collection or index."""
    if client.collection_exists(collection):
        _ensure_indexes(client, collection)
        return

    try:
        client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )
    except UnexpectedResponse as exc:
        # Another worker won the create race. Reconcile against whatever schema
        # the winning side already installed.
        if not _is_already_exists_error(exc):
            raise
        _ensure_indexes(client, collection)
        return

    # Winning side: skip the schema read and create the full index set.
    # Avoids racing a get_collection against Qdrant's collection bootstrap.
    _create_all_indexes(client, collection)


async def async_ensure_collection_and_indexes(
    client, collection: str, vector_size: int
) -> None:
    """Async mirror of :func:`ensure_collection_and_indexes`."""
    if await client.collection_exists(collection):
        await _async_ensure_indexes(client, collection)
        return

    try:
        await client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )
    except UnexpectedResponse as exc:
        if not _is_already_exists_error(exc):
            raise
        await _async_ensure_indexes(client, collection)
        return

    await _async_create_all_indexes(client, collection)


def _create_all_indexes(client, collection: str) -> None:
    _create_index_if_missing(client, collection, "ticker", _TICKER_INDEX_SCHEMA)
    _create_index_if_missing(
        client, collection, "year", models.PayloadSchemaType.INTEGER
    )
    _create_index_if_missing(
        client, collection, "item", models.PayloadSchemaType.KEYWORD
    )


async def _async_create_all_indexes(client, collection: str) -> None:
    await _async_create_index_if_missing(
        client, collection, "ticker", _TICKER_INDEX_SCHEMA
    )
    await _async_create_index_if_missing(
        client, collection, "year", models.PayloadSchemaType.INTEGER
    )
    await _async_create_index_if_missing(
        client, collection, "item", models.PayloadSchemaType.KEYWORD
    )


def _create_index_if_missing(client, collection: str, field: str, schema) -> None:
    """Create a payload index, tolerating a concurrent create that wins the race."""
    try:
        client.create_payload_index(
            collection_name=collection,
            field_name=field,
            field_schema=schema,
        )
    except UnexpectedResponse as exc:
        if not _is_already_exists_error(exc):
            raise


async def _async_create_index_if_missing(client, collection: str, field: str, schema) -> None:
    try:
        await client.create_payload_index(
            collection_name=collection,
            field_name=field,
            field_schema=schema,
        )
    except UnexpectedResponse as exc:
        if not _is_already_exists_error(exc):
            raise


def _ensure_indexes(client, collection: str) -> None:
    schema = _payload_schema(client, collection)
    ticker_entry = schema.get("ticker")
    if ticker_entry is not None and not _is_tenant_index(ticker_entry):
        try:
            client.delete_payload_index(
                collection_name=collection, field_name="ticker"
            )
        except UnexpectedResponse as exc:
            # 404 means the index was already dropped by another worker.
            if getattr(exc, "status_code", None) != 404:
                raise
        ticker_entry = None

    if ticker_entry is None:
        _create_index_if_missing(client, collection, "ticker", _TICKER_INDEX_SCHEMA)
    if "year" not in schema:
        _create_index_if_missing(
            client, collection, "year", models.PayloadSchemaType.INTEGER
        )
    if "item" not in schema:
        _create_index_if_missing(
            client, collection, "item", models.PayloadSchemaType.KEYWORD
        )


async def _async_ensure_indexes(client, collection: str) -> None:
    schema = await _async_payload_schema(client, collection)
    ticker_entry = schema.get("ticker")
    if ticker_entry is not None and not _is_tenant_index(ticker_entry):
        try:
            await client.delete_payload_index(
                collection_name=collection, field_name="ticker"
            )
        except UnexpectedResponse as exc:
            if getattr(exc, "status_code", None) != 404:
                raise
        ticker_entry = None

    if ticker_entry is None:
        await _async_create_index_if_missing(
            client, collection, "ticker", _TICKER_INDEX_SCHEMA
        )
    if "year" not in schema:
        await _async_create_index_if_missing(
            client, collection, "year", models.PayloadSchemaType.INTEGER
        )
    if "item" not in schema:
        await _async_create_index_if_missing(
            client, collection, "item", models.PayloadSchemaType.KEYWORD
        )
