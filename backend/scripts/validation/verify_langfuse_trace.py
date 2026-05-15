#!/usr/bin/env python
"""Verify a Langfuse trace satisfies an expected reasoning / abort shape.

Operator helper used by the BDD 6-case matrix and abort flow scenarios
(J-stream-01, J-trace-01, J-rsn-01/02, S-trace-06). Polls
``GET /api/public/traces/{trace_id}`` and asserts that:

- A root span (``parentObservationId is null``) exists.
- Every GENERATION observation's ``metadata.reasoning`` matches the
  passed expectation:
    * ``--expect-reasoning-on``      non-empty string, not ``<unsupported>``
    * ``--expect-reasoning-off``     empty string ``""``
    * ``--expect-unsupported``       sentinel ``"<unsupported>"``
- When ``--expect-aborted`` is passed, the root span carries
  ``metadata.status == "aborted"``. The latest GENERATION's
  ``metadata.reasoning_tail_aborted`` is checked best-effort: an empty
  buffer at abort is acceptable per design.

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


def _generations(observations: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [obs for obs in observations if obs.get("type") == "GENERATION"]


def _root_span(observations: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    # The LangChain root run lands as type="CHAIN" (Langfuse classifies the
    # outermost @observe-style chain that way), not "SPAN". Match by
    # parentObservationId=null to find the root regardless of type — but
    # exclude GENERATION since a parentless GENERATION means the LLM call
    # has no enclosing chain/turn span, which is itself a topology bug we
    # want the verifier to surface (e.g. a missing agent.run wrapper).
    for obs in observations:
        if obs.get("parentObservationId") is None and obs.get("type") != "GENERATION":
            return obs
    return None


def _check_reasoning_on(generations: list[dict[str, Any]]) -> list[str]:
    """For reasoning-on agents, assert that the always-write-key contract
    (D29 / C5.2) holds on every generation AND at least one generation
    actually carries reasoning text.

    Anthropic and OpenAI both decide per LLM call whether to emit reasoning —
    short tool-decision turns ("call get_section then look at output") often
    skip reasoning entirely while the synthesizing turn produces a long
    chain-of-thought. Requiring every generation to carry reasoning text was
    over-strict and incorrectly failed traces from those providers.
    """
    failures: list[str] = []
    has_text = False
    for gen in generations:
        meta = gen.get("metadata") or {}
        if "reasoning" not in meta:
            failures.append(f"generation {gen.get('id')} missing metadata.reasoning")
            continue
        value = meta["reasoning"]
        # Always-write-key contract: value must be a string and never the
        # unsupported sentinel for a reasoning-on agent.
        if not isinstance(value, str):
            failures.append(
                f"generation {gen.get('id')} reasoning is not a string: {value!r}"
            )
            continue
        if value == UNSUPPORTED_SENTINEL:
            failures.append(
                f"generation {gen.get('id')} expected reasoning string, got "
                f"{UNSUPPORTED_SENTINEL!r}"
            )
            continue
        if value:
            has_text = True
    if generations and not has_text:
        failures.append(
            "no generation carried non-empty reasoning text "
            "(reasoning-on agent should produce reasoning on at least one LLM call)"
        )
    return failures


def _check_reasoning_off(generations: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for gen in generations:
        meta = gen.get("metadata") or {}
        value = meta.get("reasoning")
        if value != "":
            failures.append(
                f"generation {gen.get('id')} expected empty reasoning, got {value!r}"
            )
    return failures


def _check_reasoning_unsupported(generations: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for gen in generations:
        meta = gen.get("metadata") or {}
        value = meta.get("reasoning")
        if value != UNSUPPORTED_SENTINEL:
            failures.append(
                f"generation {gen.get('id')} expected {UNSUPPORTED_SENTINEL!r}, got {value!r}"
            )
    return failures


def _latest_generation(generations: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not generations:
        return None
    # startTime sorts lexicographically as ISO-8601 UTC, so string compare is fine.
    return max(generations, key=lambda g: g.get("startTime") or "")


def verify(
    trace: dict[str, Any], *, expectation: str, expect_aborted: bool
) -> tuple[bool, list[str]]:
    """Run all assertions over a fetched trace. Returns ``(ok, errors)``."""
    observations = trace.get("observations") or []
    errors: list[str] = []

    root = _root_span(observations)
    if root is None:
        errors.append("root span (parentObservationId=null) not found")

    generations = _generations(observations)
    if not generations:
        errors.append("no GENERATION observations found")

    if expectation == "reasoning-on":
        errors.extend(_check_reasoning_on(generations))
    elif expectation == "reasoning-off":
        errors.extend(_check_reasoning_off(generations))
    elif expectation == "unsupported":
        errors.extend(_check_reasoning_unsupported(generations))

    if expect_aborted:
        if root is not None:
            root_meta = root.get("metadata") or {}
            if root_meta.get("status") != "aborted":
                errors.append(
                    f"root span metadata.status expected 'aborted', got {root_meta.get('status')!r}"
                )
        # tail-aborted is best-effort: an empty segmenter buffer at abort is
        # acceptable per design (D35). We do not fail when it's missing.
        latest = _latest_generation(generations)
        if latest is not None:
            tail = (latest.get("metadata") or {}).get("reasoning_tail_aborted")
            # Recorded for the JSON summary; not a hard assertion.
            trace.setdefault("_verifier", {})["tail_aborted_present"] = bool(tail)

    return (not errors, errors)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify a Langfuse trace satisfies an expected reasoning shape.",
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
        help="Also assert root span metadata.status == 'aborted' (S-trace-06)",
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
        "generations": len(_generations(trace.get("observations") or [])),
        "errors": errors,
    }
    print(json.dumps(summary, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
