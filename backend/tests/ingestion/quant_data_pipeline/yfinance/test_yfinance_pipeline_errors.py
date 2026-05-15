import pytest

from backend.ingestion.quant_data_pipeline.quant_pipeline_errors import (
    DataValidationError,
    QuantPipelineError,
    TickerNotFoundError,
    TransientError,
)
from backend.ingestion.quant_data_pipeline.yfinance.yfinance_pipeline_errors import (
    YFinanceEmptyResponseError,
    YFinanceRateLimitError,
    YFinanceTickerNotFoundError,
)

SUBCLASS_BASE_PAIRS = [
    (YFinanceRateLimitError, TransientError),
    (YFinanceTickerNotFoundError, TickerNotFoundError),
    (YFinanceEmptyResponseError, DataValidationError),
]

YFINANCE_ERROR_CLASSES = [pair[0] for pair in SUBCLASS_BASE_PAIRS]


@pytest.mark.parametrize("subclass,base", SUBCLASS_BASE_PAIRS)
def test_inherits_from_matching_foundation_base(subclass, base):
    assert issubclass(subclass, base)


@pytest.mark.parametrize("cls", YFINANCE_ERROR_CLASSES)
def test_inherits_from_quant_pipeline_error(cls):
    assert issubclass(cls, QuantPipelineError)
    assert issubclass(cls, Exception)


@pytest.mark.parametrize("cls", YFINANCE_ERROR_CLASSES)
def test_has_non_empty_docstring(cls):
    assert cls.__doc__ is not None
    assert cls.__doc__.strip() != ""


def test_sibling_non_inheritance():
    assert not issubclass(YFinanceRateLimitError, YFinanceEmptyResponseError)
    assert not issubclass(YFinanceEmptyResponseError, YFinanceRateLimitError)
    assert not issubclass(YFinanceRateLimitError, YFinanceTickerNotFoundError)
    assert not issubclass(YFinanceTickerNotFoundError, YFinanceRateLimitError)
    assert not issubclass(YFinanceTickerNotFoundError, YFinanceEmptyResponseError)
    assert not issubclass(YFinanceEmptyResponseError, YFinanceTickerNotFoundError)
