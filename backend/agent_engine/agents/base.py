"""Version-agnostic Orchestrator for FinLab-X.

Uses LangChain's create_agent to handle the tool calling loop automatically.
The Orchestrator does NOT manually manage bind_tools or tool execution —
create_agent handles tool schema binding and the ReAct loop internally.

Langfuse integration: A per-request CallbackHandler is injected into
invoke()/ainvoke() to auto-trace all LLM calls, tool dispatch, and chain
steps. session_id is propagated from the API layer using
propagate_attributes() so @observe()-decorated tool observations inherit it.
"""

import os
import re
import time
import uuid
from collections.abc import AsyncGenerator
from typing import Any, Literal

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ToolCallLimitMiddleware
from langchain.agents.middleware.tool_call_limit import ToolCallLimitState
from langchain.agents.middleware.types import ResponseT, hook_config
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, BaseMessage, RemoveMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from langgraph.typing import ContextT
from typing_extensions import override
from langfuse import propagate_attributes
from langfuse.langchain import CallbackHandler
from langgraph.checkpoint.base import BaseCheckpointSaver
from typing_extensions import TypedDict

from backend.agent_engine.agents.config_loader import VersionConfig
from backend.agent_engine.streaming.domain_events_schema import (
    DomainEvent,
    Finish,
    StreamError,
)
from backend.agent_engine.streaming.event_mapper import StreamEventMapper
from backend.agent_engine.streaming.tool_error_sanitizer import sanitize_tool_error
from backend.agent_engine.tools import setup_tools
from backend.agent_engine.tools.registry import get_tools_by_names
from backend.agent_engine.utils.model_context import compute_section_soft_cap_chars
from backend.common.sec_core import ConfigurationError


# Captured once per Python process. Lets engineers distinguish pre/post-restart
# traces sharing the same session_id (DD-06 silent post-restart amnesia).
_PROCESS_START_TS = time.time()


_SEC_TOOLS_REQUIRING_IDENTITY = {
    "sec_filing_list_sections",
    "sec_filing_get_section",
    "sec_filing_downloader",
}


# Matches `{identifier}` placeholders where `identifier` is a Python-style name.
# Literal JSON fragments like `{"role": "user"}` have `"` as the first inner
# char and are skipped, so they survive rendering untouched.
_PROMPT_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


_DEFAULT_SYSTEM_PROMPT = """\
You are FinLab-X, a strict, data-driven financial AI Agent.

LANGUAGE POLICY:
- All tool arguments (search queries, etc.) MUST be in English regardless of the user's language. Example: user asks "微軟最近有什麼新聞？" → search "MSFT recent news", NOT "微軟最近新聞".
- Detect the language of the user's query. Respond in that SAME language. If the user writes in Chinese, your final answer MUST be in Chinese. If the user writes in English, respond in English.

TOOL CALL BUDGET:
- You may make at most {max_tool_calls_per_run} tool calls per request (across the entire run). Plan before you call: if a question needs more data than the budget allows, prioritize the most decision-relevant calls first and summarize with what you have.
- Once the budget is exhausted, every remaining tool call in this run is blocked and you will see a ToolMessage stating "Per-run tool-call budget reached". This is an INTERNAL orchestration limit — it is NOT an external rate limit from SEC, Yahoo Finance, Tavily, or any other external API. Do NOT tell the user "I hit a rate limit" or describe it as a network/API failure.

ZERO HALLUCINATION POLICY:
- Only use data from provided tools
- If data is insufficient, say "I don't have enough information"
- Never invent financial metrics or news

CITATION REQUIREMENTS:
- Support all claims with specific data points from tool outputs
- Cite sources by tool name (e.g., "According to yfinance data...")
- Flag any data quality issues or stale data

RESPONSE FORMAT:
- Start with a clear conclusion
- Support with specific data points
- Cite sources (tool names)
- Flag any data quality issues"""


class _HandleToolErrors(AgentMiddleware):
    """Middleware that catches tool exceptions and returns sanitized error messages.

    Implements both sync and async to support invoke() (eval runner) and
    astream() (streaming API).
    """

    def wrap_tool_call(self, request, handler):
        try:
            return handler(request)
        except Exception as e:
            return ToolMessage(
                content=sanitize_tool_error(str(e)),
                tool_call_id=request.tool_call["id"],
                status="error",
            )

    async def awrap_tool_call(self, request, handler):
        try:
            return await handler(request)
        except Exception as e:
            return ToolMessage(
                content=sanitize_tool_error(str(e)),
                tool_call_id=request.tool_call["id"],
                status="error",
            )


handle_tool_errors = _HandleToolErrors()


class RunBudgetMiddleware(ToolCallLimitMiddleware[Any, Any]):
    """Per-run tool-call budget with an LLM-disambiguated error message.

    The upstream ``ToolCallLimitMiddleware`` injects a ToolMessage reading
    "Tool call limit exceeded. Do not call '<name>' again." When the model
    reads that phrase it tends to paraphrase it to the user as "I hit a
    rate limit", conflating our internal budget with a real SEC / Yahoo /
    Tavily 429. This subclass reuses the upstream counting logic via
    ``super().after_model()`` and rewrites the injected message to an
    explicit, non-ambiguous form that tells the model both (a) not to
    retry the tool, and (b) not to describe the block as a remote-service
    failure.
    """

    @staticmethod
    def _budget_message(tool_name: str | None) -> str:
        scope = f"'{tool_name}'" if tool_name else "any further tools"
        return (
            "Per-run tool-call budget reached for this request. "
            f"Do not call {scope} again in this run. "
            "This is an INTERNAL orchestration budget — it is NOT an "
            "external rate limit from SEC EDGAR, Yahoo Finance, Tavily, "
            "or any other external API. Summarize with the data already "
            "collected; do not describe this to the user as a network or "
            "API failure."
        )

    def _rewrite_messages(self, result: dict[str, Any] | None) -> dict[str, Any] | None:
        if not result or "messages" not in result:
            return result
        msg = self._budget_message(self.tool_name)
        rewritten: list[Any] = []
        for item in result["messages"]:
            if isinstance(item, ToolMessage) and item.status == "error":
                rewritten.append(
                    ToolMessage(
                        content=msg,
                        tool_call_id=item.tool_call_id,
                        name=item.name,
                        status="error",
                    )
                )
            else:
                rewritten.append(item)
        result["messages"] = rewritten
        return result

    @hook_config(can_jump_to=["end"])
    @override
    def after_model(
        self,
        state: ToolCallLimitState[ResponseT],
        runtime: Runtime[ContextT],
    ) -> dict[str, Any] | None:
        return self._rewrite_messages(super().after_model(state, runtime))

    @hook_config(can_jump_to=["end"])
    @override
    async def aafter_model(
        self,
        state: ToolCallLimitState[ResponseT],
        runtime: Runtime[ContextT],
    ) -> dict[str, Any] | None:
        return self._rewrite_messages(super().after_model(state, runtime))


class ToolOutput(TypedDict):
    tool: str
    args: dict[str, object]
    result: str


class OrchestratorResult(TypedDict):
    response: str
    tool_outputs: list[ToolOutput]
    model: str
    version: str


class _LangfusePropagationAttributes(TypedDict, total=False):
    session_id: str
    trace_name: str


class Orchestrator:
    """Version-agnostic Orchestrator that loads capabilities from config."""

    def __init__(self, config: VersionConfig, *, checkpointer: BaseCheckpointSaver | None = None):
        setup_tools()
        self._validate_edgar_identity(config)
        self.config = config
        self.tools = get_tools_by_names(config.tools)
        raw_prompt = config.system_prompt or _DEFAULT_SYSTEM_PROMPT
        self.system_prompt = self._render_prompt(
            raw_prompt,
            config.model.name,
            max_tool_calls_per_run=config.constraints.max_tool_calls_per_run,
        )

        model = init_chat_model(config.model.name, temperature=config.model.temperature)
        tool_call_limit = RunBudgetMiddleware(
            run_limit=config.constraints.max_tool_calls_per_run,
        )
        self.agent = create_agent(
            model=model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            middleware=[tool_call_limit, handle_tool_errors],
            checkpointer=checkpointer,
        )

    @staticmethod
    def _render_prompt(
        raw: str,
        model_name: str,
        *,
        max_tool_calls_per_run: int | None = None,
    ) -> str:
        """Render a system prompt template with orchestrator-provided variables.

        Supported placeholders:
        - ``{section_soft_cap_chars}`` — computed from the active model's
          context window
        - ``{max_tool_calls_per_run}`` — passed through from the version's
          ``constraints.max_tool_calls_per_run``; ``None`` means the prompt
          doesn't reference this variable (tests may omit it)

        Prompts with no placeholders are returned verbatim. Prompts referencing
        unknown variables raise ``ValueError`` so misconfiguration fails fast
        at startup.

        Uses a narrow regex match on ``{identifier}`` (Python-style names) so
        literal JSON fragments like ``{"role": "user"}`` pass through unchanged.
        """
        found = _PROMPT_PLACEHOLDER_RE.findall(raw)
        if not found:
            return raw
        provided: dict[str, object] = {
            "section_soft_cap_chars": compute_section_soft_cap_chars(model_name),
        }
        if max_tool_calls_per_run is not None:
            provided["max_tool_calls_per_run"] = max_tool_calls_per_run
        missing = set(found) - set(provided.keys())
        if missing:
            raise ValueError(
                f"Prompt references undefined variables: {sorted(missing)}"
            )
        return _PROMPT_PLACEHOLDER_RE.sub(
            lambda m: str(provided[m.group(1)]), raw
        )

    @staticmethod
    def _validate_edgar_identity(config: VersionConfig) -> None:
        """Fast-fail at startup if the version config loads a SEC tool without
        ``EDGAR_IDENTITY`` set. Versions without SEC tools skip the check so
        non-SEC deployments stay unaffected.
        """
        needs_sec = any(
            t in _SEC_TOOLS_REQUIRING_IDENTITY for t in config.tools
        )
        if needs_sec and not os.getenv("EDGAR_IDENTITY"):
            raise ConfigurationError(
                "EDGAR_IDENTITY environment variable is not set."
            )

    def run(
        self,
        prompt: str,
        *,
        session_id: str | None = None,
        request_id: str | None = None,
    ) -> OrchestratorResult:
        config, propagation = self._build_langfuse_config(
            mode="invoke",
            session_id=session_id,
            request_id=request_id or uuid.uuid4().hex,
        )
        thread_id = session_id if isinstance(session_id, str) and session_id else str(uuid.uuid4())
        config["configurable"] = {"thread_id": thread_id}
        with propagate_attributes(**propagation):
            result = self.agent.invoke(
                {"messages": [{"role": "user", "content": prompt}]},
                config=config,
            )
        return self._extract_result(result)

    async def arun(
        self,
        prompt: str,
        *,
        session_id: str | None = None,
        request_id: str | None = None,
    ) -> OrchestratorResult:
        """Execute the agent asynchronously (non-blocking).

        Use this from async FastAPI endpoints to avoid blocking the event loop.
        """
        config, propagation = self._build_langfuse_config(
            mode="invoke",
            session_id=session_id,
            request_id=request_id or uuid.uuid4().hex,
        )
        thread_id = session_id if isinstance(session_id, str) and session_id else str(uuid.uuid4())
        config["configurable"] = {"thread_id": thread_id}
        with propagate_attributes(**propagation):
            result = await self.agent.ainvoke(
                {"messages": [{"role": "user", "content": prompt}]},
                config=config,
            )
        return self._extract_result(result)

    async def astream_run(
        self,
        *,
        message: str | None = None,
        session_id: str,
        trigger: str | None = None,
        message_id: str | None = None,
        request_id: str | None = None,
    ) -> AsyncGenerator[DomainEvent, None]:
        config, propagation = self._build_langfuse_config(
            mode="stream",
            session_id=session_id,
            request_id=request_id or uuid.uuid4().hex,
            trigger=trigger,
            message_id=message_id,
        )
        config["configurable"] = {"thread_id": session_id}
        mapper = StreamEventMapper(session_id=session_id)

        with propagate_attributes(**propagation):
            try:
                if trigger == "regenerate":
                    await self._prepare_regenerate(config, message_id)
                    input_data = None
                else:
                    input_data = {"messages": [{"role": "user", "content": message}]}

                async for raw_chunk in self.agent.astream(
                    input_data,
                    config=config,
                    stream_mode=["messages", "updates", "custom"],
                    version="v2",
                ):
                    if isinstance(raw_chunk, tuple):
                        chunk = {"type": raw_chunk[0], "data": raw_chunk[1]}
                    else:
                        chunk = raw_chunk
                    for event in mapper.process_chunk(chunk):
                        yield event

                for event in mapper.finalize():
                    yield event
            except Exception as e:
                for event in mapper.finalize():
                    if not isinstance(event, Finish):
                        yield event
                yield StreamError(error_text=sanitize_tool_error(str(e)))
                yield Finish(finish_reason="error")

    @staticmethod
    def _find_regenerate_target(
        messages: list[BaseMessage], message_id: str | None
    ) -> int:
        """Find the start index of the last AI turn for regeneration.

        Walks backward to find the last contiguous block of AIMessage and
        ToolMessage entries (the "last turn"). Returns the index of the first
        AIMessage in that turn, optionally verifying that ``message_id``
        belongs to it.

        Raises ValueError if no AI messages exist or ``message_id`` is not
        in the last turn.
        """
        if not any(isinstance(m, AIMessage) for m in messages):
            raise ValueError("No assistant message to regenerate")

        last_ai_idx = None
        for i in reversed(range(len(messages))):
            if isinstance(messages[i], AIMessage):
                last_ai_idx = i
                break

        assert last_ai_idx is not None

        turn_start = last_ai_idx
        turn_ids: set[str] = set()
        for i in range(last_ai_idx, -1, -1):
            if isinstance(messages[i], AIMessage):
                turn_start = i
                turn_ids.add(messages[i].id)
            elif isinstance(messages[i], ToolMessage):
                continue
            else:
                break

        if message_id:
            if message_id not in turn_ids:
                raise ValueError(
                    "messageId does not match the last assistant message"
                )

        return turn_start

    async def validate_regenerate(
        self, *, session_id: str, message_id: str | None
    ) -> None:
        """Validate regenerate preconditions before streaming.

        Raises ValueError with descriptive message on failure.
        """
        config: dict = {"configurable": {"thread_id": session_id}}
        state = await self.agent.aget_state(config)
        messages = state.values.get("messages", [])

        if not messages:
            raise ValueError("No conversation found for this session")

        self._find_regenerate_target(messages, message_id)

    async def _prepare_regenerate(
        self, config: dict, message_id: str | None
    ) -> None:
        state = await self.agent.aget_state(config)
        messages = state.values.get("messages", [])

        target_idx = self._find_regenerate_target(messages, message_id)

        to_remove = [RemoveMessage(id=m.id) for m in messages[target_idx:]]
        await self.agent.aupdate_state(config, {"messages": to_remove}, as_node="__start__")

    def _build_langfuse_config(
        self,
        *,
        mode: Literal["invoke", "stream"],
        request_id: str,
        session_id: str | None = None,
        **extra_metadata: object,
    ) -> tuple[RunnableConfig, _LangfusePropagationAttributes]:
        """Build the LangChain RunnableConfig + propagate_attributes kwargs.

        trace_name is derived from agent version + endpoint mode, e.g.
        ``v1_baseline_stream``. request_id + extras (trigger, message_id, ...)
        go into LangChain config metadata so CallbackHandler (Langfuse ≥4.3.1)
        attaches them to the root trace via the ``langfuse_trace_name`` path.
        """
        handler = CallbackHandler()
        trace_name = f"{self.config.name}_{mode}"

        metadata: dict[str, object] = {
            "langfuse_trace_name": trace_name,
            "request_id": request_id,
            "process_start_ts": _PROCESS_START_TS,
        }
        for key, value in extra_metadata.items():
            if value is not None:
                metadata[key] = value

        propagation: _LangfusePropagationAttributes = {"trace_name": trace_name}
        if isinstance(session_id, str) and session_id:
            propagation["session_id"] = session_id

        config: RunnableConfig = {
            "callbacks": [handler],
            "run_name": "chat-turn",
            "metadata": metadata,
        }
        return config, propagation

    def _extract_result(self, agent_output: dict[str, Any]) -> OrchestratorResult:
        messages: list[BaseMessage] = agent_output.get("messages", [])

        response_text = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                content = msg.content
                response_text = content if isinstance(content, str) else str(content)
                break

        tool_outputs: list[ToolOutput] = []
        for i, msg in enumerate(messages):
            if isinstance(msg, ToolMessage):
                tool_name = msg.name or "unknown"
                tool_args: dict[str, object] = {}

                for prev_msg in reversed(messages[:i]):
                    if isinstance(prev_msg, AIMessage) and prev_msg.tool_calls:
                        for tc in prev_msg.tool_calls:
                            if tc.get("id") == msg.tool_call_id:
                                tool_name = tc["name"]
                                tool_args = tc["args"]
                                break
                        break

                content = msg.content
                result_str = content if isinstance(content, str) else str(content)
                tool_outputs.append(
                    ToolOutput(tool=tool_name, args=tool_args, result=result_str)
                )

        return OrchestratorResult(
            response=response_text,
            tool_outputs=tool_outputs,
            model=self.config.model.name,
            version=self.config.version,
        )
