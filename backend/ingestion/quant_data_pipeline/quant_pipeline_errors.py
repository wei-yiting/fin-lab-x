class QuantPipelineError(Exception):
    """Base for all quant data pipeline errors."""


class TransientError(QuantPipelineError):
    """Retryable: net blip / 5xx / rate limit."""


class TickerNotFoundError(QuantPipelineError):
    """Non-retryable: ticker absent from source."""


class DataValidationError(QuantPipelineError):
    """Non-retryable: extracted data violates schema invariants."""


class ConfigurationError(QuantPipelineError):
    """Non-retryable: missing env var / invalid universe yaml."""


class SchemaError(QuantPipelineError):
    """Non-retryable: DB schema missing or corrupted at connect time."""
