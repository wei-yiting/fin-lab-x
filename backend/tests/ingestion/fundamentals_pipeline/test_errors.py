import pytest

from backend.ingestion.fundamentals_pipeline.errors import (
    ConfigurationError,
    DataValidationError,
    FundamentalsPipelineError,
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
    assert issubclass(cls, FundamentalsPipelineError)
    assert issubclass(cls, Exception)


def test_sibling_non_inheritance():
    assert not issubclass(TransientError, TickerNotFoundError)
    assert not issubclass(TickerNotFoundError, TransientError)
