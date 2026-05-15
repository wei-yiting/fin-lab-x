from backend.ingestion.quant_data_pipeline.quant_pipeline_errors import (
    DataValidationError,
    TickerNotFoundError,
    TransientError,
)


class YFinanceRateLimitError(TransientError):
    """Yahoo 429 / cookie-limited. Retry with 60s+ base backoff."""


class YFinanceTickerNotFoundError(TickerNotFoundError):
    """yfinance.exceptions.YFTickerMissingError — ticker does not exist."""


class YFinanceEmptyResponseError(DataValidationError):
    """Empty DataFrame / missing required field (PK or total_revenue_usd)."""
