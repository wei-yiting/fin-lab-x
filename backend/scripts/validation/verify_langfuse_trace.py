#!/usr/bin/env python
"""Verify a Langfuse trace carries the trace-level reasoning transcript.

Operator helper for the F7 / ADR-0007 shape: the conversation's full
reasoning transcript lives in ONE place — ``metadata.reasoning`` on the root
span (the ``chat_turn`` span the Orchestrator owns). Polls the trace via the
Langfuse SDK API client (``get_client().api.trace.get``) and asserts:

- A root span (``parentObservationId is null``) exists and carries the
  ``reasoning`` metadata key (always-write-key contract).
- With ``--expect-reasoning-on`` (required): the transcript is non-empty,
  is not the ``"<unsupported>"`` sentinel, contains at least one
  ``=== segment N ===`` marker, and carries non-whitespace text outside the
  marker lines (a marker-only transcript is a regression).
- When ``--expect-aborted`` is passed, the root span additionally carries
  ``metadata.status == "aborted"`` and the transcript must end with the
  ``=== aborted ===`` marker (the scripted abort scenario cancels
  mid-segment).

Authentication: the Langfuse SDK reads ``LANGFUSE_PUBLIC_KEY`` /
``LANGFUSE_SECRET_KEY`` and ``LANGFUSE_BASE_URL`` (or the legacy
``LANGFUSE_HOST``; default ``https://cloud.langfuse.com``) from the
environment.

Usage:
    uv run python -m backend.scripts.validation.verify_langfuse_trace \\
        <trace_id> --expect-reasoning-on [--expect-aborted]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from typing import Any, Iterable

import httpx
from langfuse import get_client
from langfuse.api.core import ApiError

UNSUPPORTED_SENTINEL = "<unsupported>"
SEGMENT_MARKER = "=== segment 1 ==="
ABORTED_MARKER = "=== aborted ==="
POLL_ATTEMPTS = 5
POLL_INITIAL_DELAY_SECONDS = 1.0

_MARKER_LINE_RE = re.compile(r"^=== (segment \d+|aborted) ===$")


def _has_segment_text(value: str) -> bool:
    """True when at least one non-marker line carries non-whitespace text.

    Guards against marker-only transcripts (e.g. ``"=== segment 1 ===\\n"``)
    that are non-empty and marker-bearing but contain no actual reasoning."""
    return any(
        line.strip() and not _MARKER_LINE_RE.match(line) for line in value.splitlines()
    )


def fetch_trace(trace_id: str) -> dict[str, Any]:
    """Fetch a single trace from Langfuse with linear-backoff polling.

    Uses the SDK's public API client. Polls 5× with linearly increasing
    delay (1s, 2s, …) so a freshly-emitted trace has time to land in
    Langfuse storage before the verifier asserts. API/network errors
    surface as ``RuntimeError`` after the final attempt. The typed SDK
    response is converted to a plain dict (camelCase keys, matching the
    public API JSON shape) for ``verify()``.
    """
    client = get_client()
    last_error: Exception | None = None
    for attempt in range(POLL_ATTEMPTS):
        try:
            return client.api.trace.get(trace_id).dict()
        except (ApiError, httpx.HTTPError) as exc:
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
        elif not _has_segment_text(value):
            errors.append("transcript segments carry no non-whitespace text")

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
    parser.add_argument(
        "--expect-reasoning-on",
        dest="expectation",
        action="store_const",
        const="reasoning-on",
        required=True,
        help="Assert the root span carries a non-empty, segment-marked "
        "reasoning transcript",
    )
    parser.add_argument(
        "--expect-aborted",
        action="store_true",
        help="Also assert root span metadata.status == 'aborted' and that "
        "the transcript ends with the aborted marker",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        trace = fetch_trace(args.trace_id)
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
