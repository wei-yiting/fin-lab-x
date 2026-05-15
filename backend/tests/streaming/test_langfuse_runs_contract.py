"""Langfuse SDK contract guard for ``CallbackHandler._runs``.

``reasoning_trace_callback.on_llm_end`` and ``Orchestrator._handle_abort_cleanup``
both reach into ``langfuse.langchain.CallbackHandler._runs`` to look up the
in-flight ``LangfuseGeneration`` / ``LangfuseChain`` for the current run_id.
That attribute is private SDK state — Langfuse can rename or restructure it
without bumping the public API surface. This test pins the contract so a
Langfuse upgrade that drops or refactors ``_runs`` fails CI with a clear
message instead of silently breaking reasoning persistence and abort marking
in production.

We deliberately drive Langfuse's REAL bookkeeping path (``on_chain_start`` and
``on_chat_model_start``) instead of writing sentinels into ``_runs`` directly:
the goal is to catch SDK drift along the dimensions production actually
depends on — the dict key shape (UUID vs ``str(uuid)``), and the concrete
observation type (``LangfuseChain`` for chains, ``LangfuseGeneration`` for
chat-model calls). A test that only inserts sentinels would pass even if
Langfuse normalized keys to strings or wrapped observations in a struct, and
production would silently fall through to the OTel-current-span path that
has the documented async-context bug.

The pinned invariants:

1. ``CallbackHandler`` exposes ``_runs`` on every instance.
2. ``_runs`` behaves as a ``MutableMapping`` (dict-like) keyed by ``run_id``.
3. ``LangfuseGeneration`` and ``LangfuseChain`` are importable from the
   top-level ``langfuse`` namespace.
4. After ``on_chain_start(run_id=R)`` returns, ``_runs[R]`` (EXACT UUID key,
   not ``str(R)``) is a ``LangfuseChain``. This is the invariant
   ``_handle_abort_cleanup`` relies on when it iterates ``_runs.values()`` to
   find the trace-root chain.
5. After ``on_chat_model_start(run_id=R)`` returns, ``_runs[R]`` is a
   ``LangfuseGeneration``. This is the invariant
   ``ReasoningTraceCallback.on_llm_end`` relies on when it indexes by run_id
   to attach ``metadata.reasoning`` to the matching generation.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import cast
from uuid import uuid4

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


# ---------------------------------------------------------------------------
# Real-bookkeeping-path contract: drive Langfuse's on_* hooks and assert that
# the UUID key + concrete observation type land where production reads them.
# A sentinel-only test (above) would pass even if Langfuse normalized keys to
# str(uuid) or wrapped observations in a struct, and production would silently
# fall through to the buggy OTel-current-span path. These tests fail loudly
# when SDK drift breaks either dimension.
# ---------------------------------------------------------------------------


def test_on_chain_start_populates_runs_with_uuid_key_and_chain_value(
    _langfuse_credentials: None,
) -> None:
    """``on_chain_start`` must store the chain observation under the EXACT
    UUID key — not ``str(run_id)``, not ``run_id.hex``. This is the invariant
    ``Orchestrator._handle_abort_cleanup`` relies on when it iterates
    ``handler._runs.values()`` looking for the root LangfuseChain."""
    from langfuse import LangfuseChain
    from langfuse.langchain import CallbackHandler

    handler = CallbackHandler()
    rid = uuid4()

    handler.on_chain_start(
        serialized={"name": "chat-turn"},
        inputs={"messages": []},
        run_id=rid,
        parent_run_id=None,
    )

    # Production lookup shape #1: iteration over .values() with isinstance()
    # narrowing — _handle_abort_cleanup picks the LangfuseChain root this way.
    chain_values = [v for v in handler._runs.values() if isinstance(v, LangfuseChain)]
    assert len(chain_values) == 1, (
        f"on_chain_start did not produce exactly one LangfuseChain in _runs; "
        f"got values of types: {[type(v).__name__ for v in handler._runs.values()]}. "
        "Orchestrator._handle_abort_cleanup will fail to mark the trace as "
        "aborted if the SDK no longer registers root chains here."
    )

    # Production lookup shape #2: exact UUID key indexing. If a future
    # Langfuse normalizes keys to str(uuid) or .hex, this assertion fails and
    # we can switch the production lookup helper before any silent drift.
    assert rid in handler._runs, (
        f"on_chain_start did not key the chain under the exact UUID {rid!r} — "
        f"keys actually present are types {[type(k).__name__ for k in handler._runs.keys()]}. "
        "ReasoningTraceCallback / _handle_abort_cleanup will miss the "
        "observation if the key shape drifted; update _lookup_generation_by_run_id "
        "in reasoning_trace_callback.py to match the new shape."
    )
    assert isinstance(handler._runs[rid], LangfuseChain), (
        f"_runs[{rid!r}] expected LangfuseChain, got "
        f"{type(handler._runs[rid]).__name__}. The abort-path code in "
        "Orchestrator._handle_abort_cleanup discriminates between chains and "
        "generations by isinstance — a new wrapper class would break that."
    )


def test_on_chat_model_start_populates_runs_with_uuid_key_and_generation_value(
    _langfuse_credentials: None,
) -> None:
    """``on_chat_model_start`` must store the chat-model generation under the
    EXACT UUID key. ``ReasoningTraceCallback.on_llm_end`` looks the
    generation up via ``self._handler._runs.get(run_id)`` and writes
    ``metadata.reasoning`` onto it. If Langfuse drifts the key shape, the
    lookup falls through to the OTel-current-span path which silently
    no-ops on async dispatch — every reasoning trace would lose its
    metadata without any test noticing."""
    from langchain_core.messages import HumanMessage

    from langfuse import LangfuseGeneration
    from langfuse.langchain import CallbackHandler

    handler = CallbackHandler()
    chain_rid = uuid4()
    chat_rid = uuid4()

    # The handler expects a parent chain registered before a chat-model call
    # so its internal parent-link bookkeeping has something to point at.
    handler.on_chain_start(
        serialized={"name": "chat-turn"},
        inputs={"messages": []},
        run_id=chain_rid,
        parent_run_id=None,
    )
    # Langfuse's internal _parse_model_parameters raises KeyError without
    # invocation_params (Langfuse 4.5 CallbackHandler.py:1232). The
    # exception is caught and logged by the SDK, but it short-circuits the
    # _attach_observation call — so we must provide invocation_params here
    # to drive the real bookkeeping path. Real LangChain dispatch always
    # passes this kwarg; we mirror that.
    handler.on_chat_model_start(
        serialized={"name": "openai-chat"},
        messages=[[HumanMessage(content="hi")]],
        run_id=chat_rid,
        parent_run_id=chain_rid,
        invocation_params={"_type": "openai-chat", "model_name": "gpt-test"},
    )

    # Production lookup shape: exact UUID key indexing —
    # reasoning_trace_callback.on_llm_end:
    #     generation = self._handler._runs.get(run_id)
    #     if isinstance(generation, LangfuseGeneration):
    #         generation.update(metadata={...})
    assert chat_rid in handler._runs, (
        f"on_chat_model_start did not key the generation under the exact "
        f"UUID {chat_rid!r}. Keys actually present: "
        f"{[type(k).__name__ for k in handler._runs.keys()]}. "
        "ReasoningTraceCallback.on_llm_end's _handler._runs.get(run_id) "
        "lookup will silently miss; metadata.reasoning will stop being "
        "written. Update _lookup_generation_by_run_id in "
        "reasoning_trace_callback.py to match the new key shape."
    )
    generation = handler._runs[chat_rid]
    assert isinstance(generation, LangfuseGeneration), (
        f"_runs[{chat_rid!r}] expected LangfuseGeneration, got "
        f"{type(generation).__name__}. "
        "ReasoningTraceCallback's isinstance() narrowing will fall through "
        "to update_current_generation(), which silently no-ops on async "
        "dispatch — every reasoning trace would lose metadata."
    )

    # And string-normalized keys must NOT be present today. If this
    # assertion ever flips (Langfuse switches to str keys), the
    # str-fallback in _lookup_generation_by_run_id will take over and the
    # warning log will tell ops to update the contract test.
    assert str(chat_rid) not in handler._runs, (
        "Langfuse's _runs is now keyed by str(uuid) in addition to UUID — "
        "this means the SDK changed its bookkeeping. Update the production "
        "lookup helper and remove the str-key fallback if str became the "
        "primary key shape."
    )
