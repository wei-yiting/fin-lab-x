"""Shared retry policy — single tenacity-based retry helper for FinLab-X.

Retries only :class:`~backend.common.errors.TransientError` (network blips,
upstream 5xx) with exponential backoff plus jitter, up to 2 attempts total
(single retry, per design-envelope §2),
re-raising the last failure unchanged if every attempt fails. Permanent
failures (ticker-not-found, configuration errors) and rate limits are not
:class:`TransientError` subclasses, so they propagate on the first attempt —
retrying them would only waste time on a request that can never succeed.

Apply as a decorator: ``@retry_transient`` on any function that may raise
``TransientError``. Tests can override timing with
``retry_transient.retry_with(wait=wait_none())`` — see tenacity's
``retry_with`` for per-call overrides.
"""

import logging

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from backend.common.errors import TransientError

logger = logging.getLogger(__name__)

retry_transient = retry(
    retry=retry_if_exception_type(TransientError),
    stop=stop_after_attempt(2),
    wait=wait_exponential_jitter(),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
