class FundamentalsPipelineError(Exception):
    """Base for all fundamentals pipeline errors."""


class TransientError(FundamentalsPipelineError):
    """Retryable: net blip / 5xx / rate limit."""


class TickerNotFoundError(FundamentalsPipelineError):
    """Non-retryable: ticker absent from source."""


class DataValidationError(FundamentalsPipelineError):
    """Non-retryable: extracted data violates schema invariants."""


class ConfigurationError(FundamentalsPipelineError):
    """Non-retryable: missing env var / invalid universe yaml."""


class SchemaError(FundamentalsPipelineError):
    """Non-retryable: DB schema missing or corrupted at connect time."""
