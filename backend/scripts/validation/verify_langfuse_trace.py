#!/usr/bin/env python
"""Verify a Langfuse trace carries the trace-level reasoning transcript.

Operator helper for the F7 / ADR-0007 shape: the conversation's full
reasoning transcript lives in ONE place — ``metadata.reasoning`` on the root
span (the ``chat_turn`` span the Orchestrator owns). Polls
``GET /api/public/traces/{trace_id}`` and asserts:

- A root span (``parentObservationId is null``) exists and carries the
  ``reasoning`` metadata key (always-write-key contract).
- The value matches the passed expectation:
    * ``--expect-reasoning-on``      non-empty transcript containing at
      least one ``=== segment N ===`` marker
    * ``--expect-reasoning-off``     empty string ``""``
    * ``--expect-unsupported``       sentinel ``"<unsupported>"``
- When ``--expect-aborted`` is passed, the root span additionally carries
  ``metadata.status == "aborted"``; combined with ``--expect-reasoning-on``
  (the scripted abort scenario cancels mid-segment) the transcript must end
  with the ``=== aborted ===`` marker.

Authentication: ``LANGFUSE_PUBLIC_KEY`` / ``LANGFUSE_SECRET_KEY`` env
vars (HTTP Basic). ``LANGFUSE_API_BASE`` defaults to
``https://cloud.langfuse.com``.

Usage:
    uv run python -m backend.scripts.validation.verify_langfuse_trace \\
        <trace_id> --expect-reasoning-on [--expect-aborted]
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Iterable

DEFAULT_BASE_URL = "https://cloud.langfuse.com"
UNSUPPORTED_SENTINEL = "<unsupported>"
SEGMENT_MARKER = "=== segment 1 ==="
ABORTED_MARKER = "=== aborted ==="
POLL_ATTEMPTS = 5
POLL_INITIAL_DELAY_SECONDS = 1.0


def fetch_trace(
    trace_id: str,
    *,
    base_url: str,
    public_key: str,
    secret_key: str,
) -> dict[str, Any]:
    """Fetch a single trace JSON from Langfuse with linear-backoff polling.

    Polls 5× with linearly increasing delay (1s, 2s, …) so a freshly-emitted
    trace has time to land in Langfuse storage before the verifier asserts.
    Network/HTTP errors surface as ``RuntimeError`` after the final attempt.
    """
    url = f"{base_url.rstrip('/')}/api/public/traces/{trace_id}"
    auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}"}

    last_error: Exception | None = None
    for attempt in range(POLL_ATTEMPTS):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < POLL_ATTEMPTS - 1:
                time.sleep(POLL_INITIAL_DELAY_SECONDS * (attempt + 1))
    raise RuntimeError(
        f"Langfuse trace {trace_id} unreachable after {POLL_ATTEMPTS} attempts: {last_error}"
    )


def _root_span(observations: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    # The Orchestrator-owned chat_turn span is the parentless root. Exclude
    # GENERATION: a parentless GENERATION means the LLM call has no enclosing
    # turn span, which is itself a topology bug the verifier should surface.
    for obs in observations:
        if obs.get("parentObservationId") is None and obs.get("type") != "GENERATION":
            return obs
    return None


def verify(
    trace: dict[str, Any], *, expectation: str, expect_aborted: bool
) -> tuple[bool, list[str]]:
    """Run all assertions over a fetched trace. Returns ``(ok, errors)``."""
    observations = trace.get("observations") or []
    errors: list[str] = []

    root = _root_span(observations)
    if root is None:
        errors.append("root span (parentObservationId=null) not found")
        return (False, errors)

    meta = root.get("metadata") or {}
    if "reasoning" not in meta:
        errors.append("root span missing metadata.reasoning (always-write-key)")
        return (False, errors)

    value = meta["reasoning"]
    if not isinstance(value, str):
        errors.append(f"metadata.reasoning is not a string: {value!r}")
        return (False, errors)

    if expectation == "reasoning-on":
        if value == UNSUPPORTED_SENTINEL:
            errors.append(
                f"expected reasoning transcript, got {UNSUPPORTED_SENTINEL!r}"
            )
        elif not value:
            errors.append("expected non-empty reasoning transcript, got ''")
        elif SEGMENT_MARKER not in value:
            errors.append(f"transcript carries no {SEGMENT_MARKER!r} segment marker")
    elif expectation == "reasoning-off":
        if value != "":
            errors.append(f"expected empty reasoning, got {value!r}")
    elif expectation == "unsupported":
        if value != UNSUPPORTED_SENTINEL:
            errors.append(f"expected {UNSUPPORTED_SENTINEL!r}, got {value!r}")

    if expect_aborted:
        if meta.get("status") != "aborted":
            errors.append(
                f"root span metadata.status expected 'aborted', got {meta.get('status')!r}"
            )
        # The scripted abort scenario cancels mid-segment, so the tail must
        # close with the transcript-integrity marker.
        if expectation == "reasoning-on" and not value.endswith(ABORTED_MARKER):
            errors.append(f"aborted transcript does not end with {ABORTED_MARKER!r}")

    return (not errors, errors)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify a Langfuse trace carries the trace-level reasoning transcript.",
    )
    parser.add_argument("trace_id", help="Langfuse trace id to verify")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--expect-reasoning-on",
        dest="expectation",
        action="store_const",
        const="reasoning-on",
    )
    group.add_argument(
        "--expect-reasoning-off",
        dest="expectation",
        action="store_const",
        const="reasoning-off",
    )
    group.add_argument(
        "--expect-unsupported",
        dest="expectation",
        action="store_const",
        const="unsupported",
    )
    parser.add_argument(
        "--expect-aborted",
        action="store_true",
        help="Also assert root span metadata.status == 'aborted' and (with "
        "--expect-reasoning-on) that the transcript ends with the aborted marker",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    # LANGFUSE_BASE_URL is the env var the Langfuse SDK / .env conventionally
    # uses; LANGFUSE_API_BASE is kept as a back-compat alias.
    base_url = (
        os.environ.get("LANGFUSE_BASE_URL")
        or os.environ.get("LANGFUSE_API_BASE")
        or DEFAULT_BASE_URL
    )
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")

    try:
        trace = fetch_trace(
            args.trace_id,
            base_url=base_url,
            public_key=public_key,
            secret_key=secret_key,
        )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    ok, errors = verify(
        trace, expectation=args.expectation, expect_aborted=args.expect_aborted
    )

    summary = {
        "ok": ok,
        "trace_id": trace.get("id"),
        "expectation": args.expectation,
        "expect_aborted": args.expect_aborted,
        "errors": errors,
    }
    print(json.dumps(summary, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
