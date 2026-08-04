#!/usr/bin/env python
"""Helper for BDD verification: look up the most recent Langfuse trace_id
for a given session_id, polling until found.

Usage:
    uv run python artifacts/current/temp/find_trace_by_session.py <session_id>
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Load .env so LANGFUSE_* keys are available without explicit env wiring.
load_dotenv(Path(__file__).resolve().parents[3] / "backend" / ".env")

from langfuse import Langfuse  # noqa: E402

POLL_ATTEMPTS = 8
POLL_DELAY = 2.0


def find_trace_id(session_id: str) -> str | None:
    base_url = os.environ.get("LANGFUSE_BASE_URL") or os.environ.get(
        "LANGFUSE_API_BASE", "https://cloud.langfuse.com"
    )
    client = Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        host=base_url,
    )
    for attempt in range(POLL_ATTEMPTS):
        try:
            page = client.api.trace.list(session_id=session_id, limit=5)
            traces = list(page.data) if page and getattr(page, "data", None) else []
            if traces:
                # Most recent first by timestamp; defensive sort.
                traces.sort(key=lambda t: getattr(t, "timestamp", "") or "", reverse=True)
                return traces[0].id
        except Exception as exc:  # pragma: no cover — defensive
            print(f"poll attempt {attempt + 1} failed: {exc}", file=sys.stderr)
        time.sleep(POLL_DELAY)
    return None


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: find_trace_by_session.py <session_id>", file=sys.stderr)
        return 2
    session_id = argv[1]
    trace_id = find_trace_id(session_id)
    if trace_id is None:
        print(f"no trace found for session_id={session_id}", file=sys.stderr)
        return 1
    print(trace_id)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
