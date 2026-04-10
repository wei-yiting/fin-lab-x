import importlib
import sys
from unittest.mock import AsyncMock, MagicMock, patch


def test_run_sec_retrieval_no_filters() -> None:
    """Verify eval task calls search() without filters argument."""
    mock_search = AsyncMock(return_value=[])
    mock_client = MagicMock()
    mock_client.collection_exists.return_value = True
    mock_client.count.return_value = MagicMock(count=10)

    # Clear cached module so the patched QdrantClient is used on import
    sys.modules.pop("backend.evals.eval_tasks", None)

    with (
        patch("qdrant_client.QdrantClient", return_value=mock_client),
        patch(
            "backend.ingestion.sec_dense_pipeline.retriever.search",
            mock_search,
        ),
    ):
        from backend.evals import eval_tasks

        importlib.reload(eval_tasks)
        eval_tasks.run_sec_retrieval(input={"question": "test query"})

    mock_search.assert_called_once()
    call_kwargs = mock_search.call_args
    if "filters" in (call_kwargs.kwargs or {}):
        assert call_kwargs.kwargs["filters"] is None
