import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from backend.ingestion.quant_data_pipeline.quant_pipeline_errors import TransientError

T = TypeVar("T")

logger = logging.getLogger(__name__)


def with_retry(
    max_attempts: int = 3,
    base_delay_seconds: float = 1.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry TransientError (and subclasses) with exponential backoff.

    Non-transient exceptions propagate immediately. Retry count is NOT
    written to ingestion_runs.metadata by this decorator; callers track it
    themselves if needed.
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            last_exc: TransientError | None = None
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except TransientError as exc:
                    last_exc = exc
                    if attempt + 1 >= max_attempts:
                        break
                    delay = base_delay_seconds * (2**attempt)
                    logger.warning(
                        "Transient error on attempt %d/%d for %s: %s. Retrying in %.1fs.",
                        attempt + 1,
                        max_attempts,
                        fn.__qualname__,
                        exc,
                        delay,
                    )
                    time.sleep(delay)
            assert last_exc is not None  # unreachable, appeases type checker
            raise last_exc

        return wrapper

    return decorator
