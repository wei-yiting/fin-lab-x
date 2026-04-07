"""Sanitize tool errors before exposing to end users.

Strips API keys, internal paths/hostnames, connection strings, and stack traces
while preserving enough description for user understanding.
"""

from __future__ import annotations

import re

_TRACEBACK_PREFIX = re.compile(
    r"Traceback \(most recent call last\):.*\n(?:\s+.*\n)*",
    re.MULTILINE,
)

_API_KEY_PATTERNS: list[re.Pattern[str]] = [
    # Bearer tokens
    re.compile(r"Bearer\s+\S+", re.IGNORECASE),
    # sk-* style keys (OpenAI, etc.)
    re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b"),
    # KEY=value or key=value assignments (common in config errors)
    re.compile(r"\b[A-Z_]*(?:KEY|SECRET|TOKEN|PASSWORD)\s*=\s*\S+", re.IGNORECASE),
    # ?api_key=... query parameters
    re.compile(r"[?&]api_key=[^\s&]+", re.IGNORECASE),
]

_CONNECTION_STRING = re.compile(
    r"\w+://[^\s@]*@[^\s]+",
)

_UNIX_PATH = re.compile(r"(?:/[\w._-]+){3,}")

_WINDOWS_PATH = re.compile(r"[A-Z]:\\(?:[\w._-]+\\){2,}[\w._-]*")

_INTERNAL_HOSTNAME = re.compile(
    r"\b(?:[\w-]+\.internal(?:\.[\w-]+)*|internal(?:\.[\w-]+)+)(?::\d+)?\b",
)


def sanitize_tool_error(raw_error: str) -> str:
    """Remove API keys, internal paths/hostnames, connection strings, stack traces.

    Preserves enough description for user understanding
    (e.g., 'yfinance API timeout').
    """
    if not raw_error:
        return raw_error

    result = raw_error

    # Strip stack traces first — keep only the final error line
    if "Traceback (most recent call last):" in result:
        result = _TRACEBACK_PREFIX.sub("", result)

    # Strip connection strings (before path removal, since they contain paths)
    result = _CONNECTION_STRING.sub("[connection_string]", result)

    # Strip API keys / tokens / secrets
    for pattern in _API_KEY_PATTERNS:
        result = pattern.sub("[REDACTED]", result)

    # Strip internal hostnames
    result = _INTERNAL_HOSTNAME.sub("[internal_host]", result)

    # Strip filesystem paths
    result = _UNIX_PATH.sub("[path]", result)
    result = _WINDOWS_PATH.sub("[path]", result)

    # Clean up multiple consecutive whitespace (from removals)
    result = re.sub(r"  +", " ", result)

    return result.strip()
