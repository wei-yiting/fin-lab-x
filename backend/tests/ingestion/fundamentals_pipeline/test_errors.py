import pytest

from backend.common.errors import FinLabError
from backend.ingestion.fundamentals_pipeline.errors import (
    DataValidationError,
    FundamentalsPipelineError,
    SchemaError,
)

SUBCLASSES = [
    DataValidationError,
    SchemaError,
]


@pytest.mark.parametrize("cls", SUBCLASSES)
def test_subclass_inherits_from_base_and_finlab_error(cls):
    assert issubclass(cls, FundamentalsPipelineError)
    assert issubclass(cls, FinLabError)


def test_fundamentals_pipeline_error_inherits_from_finlab_error():
    assert issubclass(FundamentalsPipelineError, FinLabError)
