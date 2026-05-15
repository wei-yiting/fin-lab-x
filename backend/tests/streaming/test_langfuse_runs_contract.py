"""Langfuse SDK contract guard for ``CallbackHandler._runs``.

``reasoning_trace_callback.on_llm_end`` and ``Orchestrator._handle_abort_cleanup``
both reach into ``langfuse.langchain.CallbackHandler._runs`` to look up the
in-flight ``LangfuseGeneration`` / ``LangfuseChain`` for the current run_id.
That attribute is private SDK state — Langfuse can rename or restructure it
without bumping the public API surface. This test pins the contract so a
Langfuse upgrade that drops or refactors ``_runs`` fails CI with a clear
message instead of silently breaking reasoning persistence and abort marking
in production.

The pinned invariants:

1. The class exposes a ``_runs`` attribute on every instance.
2. ``_runs`` behaves as a ``MutableMapping`` (dict-like) keyed by ``run_id``.
3. The runtime types we narrow ``_runs.values()`` against —
   ``langfuse.LangfuseGeneration`` and ``langfuse.LangfuseChain`` — are
   importable from the top-level ``langfuse`` namespace.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import cast

import pytest

# Marker is registered in pyproject.toml so the test is discoverable as
# ``-m langfuse_internal_contract`` for targeted runs after SDK upgrades.
pytestmark = pytest.mark.langfuse_internal_contract


@pytest.fixture
def _langfuse_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set throwaway credentials so ``CallbackHandler()`` can construct
    without touching real Langfuse infrastructure. The handler defers any
    network I/O to ingestion time, so instantiation alone is safe."""
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-contract-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-contract-test")
    monkeypatch.setenv("LANGFUSE_HOST", "http://localhost:3000")


def test_callback_handler_exposes_runs_attribute(_langfuse_credentials: None) -> None:
    """The handler must carry a ``_runs`` attribute that our code can read."""
    from langfuse.langchain import CallbackHandler

    handler = CallbackHandler()
    assert hasattr(handler, "_runs"), (
        "langfuse.langchain.CallbackHandler no longer exposes '_runs' — "
        "reasoning_trace_callback.on_llm_end and Orchestrator._handle_abort_cleanup "
        "rely on this attribute to look up in-flight LangfuseGeneration / "
        "LangfuseChain observations by run_id. A Langfuse upgrade likely "
        "renamed or removed this internal state; update both call sites to "
        "match the new SDK contract before bumping the dependency."
    )


def test_runs_is_a_mutable_mapping(_langfuse_credentials: None) -> None:
    """``_runs`` must behave as a dict-like mapping so we can iterate
    ``.values()`` and key into it by ``run_id``."""
    from langfuse.langchain import CallbackHandler

    handler = CallbackHandler()
    runs = cast(object, handler._runs)
    assert isinstance(runs, MutableMapping), (
        f"langfuse.langchain.CallbackHandler._runs changed type to "
        f"{type(runs).__name__!r} (expected MutableMapping). "
        "Orchestrator._handle_abort_cleanup iterates handler._runs.values() "
        "and ReasoningTraceCallback.on_llm_end keys into it by run_id — "
        "both will break if _runs is no longer dict-like."
    )


def test_runtime_observation_types_importable() -> None:
    """The narrowing types used in ``_handle_abort_cleanup`` and
    ``reasoning_trace_callback`` must remain importable from the top-level
    ``langfuse`` namespace — that's how the code distinguishes a root chain
    observation from an in-flight generation when iterating ``_runs``."""
    from langfuse import LangfuseChain, LangfuseGeneration

    # The two classes participate in isinstance() checks against _runs
    # values, so they must be real classes, not stubs.
    assert isinstance(LangfuseGeneration, type), (
        f"langfuse.LangfuseGeneration is not a class: {type(LangfuseGeneration).__name__}"
    )
    assert isinstance(LangfuseChain, type), (
        f"langfuse.LangfuseChain is not a class: {type(LangfuseChain).__name__}"
    )


def test_runs_accepts_uuid_keyed_writes(_langfuse_credentials: None) -> None:
    """Smoke-check the mapping protocol: a freshly constructed handler has
    an empty ``_runs`` we can assign into. This pins the assumption in
    ``reasoning_trace_callback.on_llm_end`` that we may directly index
    ``handler._runs[run_id]`` to retrieve the matching observation."""
    from uuid import uuid4

    from langfuse.langchain import CallbackHandler

    handler = CallbackHandler()
    assert len(handler._runs) == 0, (
        "Fresh CallbackHandler._runs is not empty — Langfuse may have changed "
        "construction semantics; verify ReasoningTraceCallback still keys "
        "into the same dict the SDK populates on handler hooks."
    )

    sentinel = object()
    rid = uuid4()
    handler._runs[rid] = sentinel  # type: ignore[assignment]
    assert handler._runs[rid] is sentinel
    assert rid in handler._runs

    # Cleanup so we don't leak this fake observation into any shared state
    # — _runs is a per-instance dict, but be explicit anyway.
    del handler._runs[rid]
