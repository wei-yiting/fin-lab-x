import pytest

from backend.ingestion.quant_data_pipeline.quant_pipeline_errors import (
    ConfigurationError,
    DataValidationError,
    QuantPipelineError,
    SchemaError,
    TickerNotFoundError,
    TransientError,
)

SUBCLASSES = [
    TransientError,
    TickerNotFoundError,
    DataValidationError,
    ConfigurationError,
    SchemaError,
]


@pytest.mark.parametrize("cls", SUBCLASSES)
def test_subclass_inherits_from_base_and_exception(cls):
    assert issubclass(cls, QuantPipelineError)
    assert issubclass(cls, Exception)


def test_sibling_non_inheritance():
    assert not issubclass(TransientError, TickerNotFoundError)
    assert not issubclass(TickerNotFoundError, TransientError)
