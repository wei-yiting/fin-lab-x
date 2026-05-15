"""yfinance subsystem tuning knobs.

PACING_MIN_INTERVAL_SECONDS gates outbound HTTP calls. RETRY_BASE_DELAY_SECONDS
is intentionally 60s (not the foundation default of 1s) because Yahoo enforces
a long rate-limit window — shorter backoff triggers immediate re-block.
"""

PACING_MIN_INTERVAL_SECONDS: float = 1.0
RETRY_MAX_ATTEMPTS: int = 3
RETRY_BASE_DELAY_SECONDS: float = 60.0
YF_NETWORK_RETRIES: int = 2
