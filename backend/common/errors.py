"""Shared error taxonomy — single definition point for FinLab-X.

:class:`FinLabError` is the top-level base every domain error ultimately
inherits from, so a CLI or handler layer can catch one class and mean "any
expected domain failure." :class:`TransientError`, :class:`TickerNotFoundError`,
:class:`ConfigurationError`, and :class:`RateLimitError` are cross-subsystem
concepts (any data source can hit a transient failure, an unknown identifier,
missing config, or a rate limit) and are defined exactly once here.

Subsystem bases (e.g. ``SECError``, ``FundamentalsPipelineError``) subclass
:class:`FinLabError` directly and keep only errors specific to that
subsystem — they must not redefine any of the four shared classes above.
"""


class FinLabError(Exception):
    """Top-level base for all FinLab-X domain errors."""


class TransientError(FinLabError):
    """A retryable failure — network blip, upstream 5xx, etc."""


class TickerNotFoundError(FinLabError):
    """The requested ticker does not exist or has no relevant data."""


class ConfigurationError(FinLabError):
    """Required configuration (env var, credential, config file) is missing or invalid."""


class RateLimitError(FinLabError):
    """An upstream source rate-limited the request. Not retried — callers fail fast.

    Carries ``retry_after`` (seconds) when the source's response included a
    ``Retry-After`` header; ``None`` means the source did not provide one.
    """

    def __init__(self, source: str, retry_after: int | None = None) -> None:
        self.retry_after = retry_after
        msg = f"Rate-limited by {source}"
        if retry_after is not None:
            msg += f" (Retry-After={retry_after}s)"
        super().__init__(msg)
