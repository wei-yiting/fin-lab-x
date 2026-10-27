"""Unit test for the marker-check helper in common.py: a Qdrant lookup
failure must propagate to the caller, never be folded into a False (which
would look identical to a genuine "not ingested yet" miss).

The genuine-miss (empty result / incomplete marker -> False) half of this
contract is already covered end-to-end against a real Qdrant instance in
integration/test_ingest.py and integration/test_search.py.
"""

from unittest.mock import AsyncMock

import pytest

from backend.ingestion.sec_dense_pipeline.common import (
    async_check_commit_marker_complete,
)


@pytest.mark.asyncio
async def test_async_check_commit_marker_complete_propagates_retrieve_failure():
    client = AsyncMock()
    client.retrieve = AsyncMock(side_effect=RuntimeError("Qdrant unreachable"))
    with pytest.raises(RuntimeError, match="Qdrant unreachable"):
        await async_check_commit_marker_complete(client, "collection", "AAPL", 2024)
