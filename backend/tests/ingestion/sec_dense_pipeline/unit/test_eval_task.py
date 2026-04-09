from unittest.mock import AsyncMock, patch


def test_run_sec_retrieval_no_filters() -> None:
    """Verify eval task calls search() without filters argument."""
    mock_search = AsyncMock(return_value=[])
    with patch(
        "backend.ingestion.sec_dense_pipeline.retriever.search", mock_search
    ):
        from backend.evals.eval_tasks import run_sec_retrieval

        run_sec_retrieval(input={"question": "test query"})

    mock_search.assert_called_once()
    call_kwargs = mock_search.call_args
    if "filters" in (call_kwargs.kwargs or {}):
        assert call_kwargs.kwargs["filters"] is None
