from backend.common.errors import FinLabError


class FundamentalsPipelineError(FinLabError):
    """Base for all fundamentals pipeline errors."""


class DataValidationError(FundamentalsPipelineError):
    """Non-retryable: extracted data violates schema invariants."""


class SchemaError(FundamentalsPipelineError):
    """Non-retryable: DB schema missing or corrupted at connect time."""
