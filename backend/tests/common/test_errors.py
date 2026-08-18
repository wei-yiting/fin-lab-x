"""Single-definition-point acceptance tests for the shared error taxonomy.

Two subsystems (SEC ingestion, fundamentals ingestion) each raise shared
error classes; these tests assert both resolve the exact same class object
and that a single `except FinLabError` catches failures from either
subsystem — the executable proof that there is only one definition.
"""

import pytest

from backend.common.errors import ConfigurationError as CommonConfigurationError
from backend.common.errors import FinLabError
from backend.common.errors import TransientError as CommonTransientError
from backend.common.sec_core import ConfigurationError as SecConfigurationError
from backend.common.sec_core import SECError
from backend.ingestion.fundamentals_pipeline.errors import FundamentalsPipelineError
from backend.ingestion.fundamentals_pipeline.ticker_universe_loader import (
    ConfigurationError as LoaderConfigurationError,
)
from backend.ingestion.sec_filing_pipeline_html.pipeline import (
    TransientError as PipelineTransientError,
)


def test_configuration_error_is_a_single_object_across_subsystems():
    assert CommonConfigurationError is SecConfigurationError is LoaderConfigurationError


def test_transient_error_is_a_single_object_across_import_paths():
    assert CommonTransientError is PipelineTransientError


def test_sec_error_and_fundamentals_pipeline_error_both_extend_finlab_error():
    assert issubclass(SECError, FinLabError)
    assert issubclass(FundamentalsPipelineError, FinLabError)


def test_finlab_error_catches_both_subsystem_bases():
    for exc in (SECError("sec failure"), FundamentalsPipelineError("fp failure")):
        with pytest.raises(FinLabError):
            raise exc
