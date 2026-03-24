"""Version-agnostic Orchestrator for FinLab-X.

Uses LangChain's create_agent to handle the tool calling loop automatically.
The Orchestrator does NOT manually manage bind_tools or tool execution —
create_agent handles tool schema binding and the ReAct loop internally.

Langfuse integration: A per-request CallbackHandler is injected into
invoke()/ainvoke() to auto-trace all LLM calls, tool dispatch, and chain
steps. session_id is propagated from the API layer using
propagate_attributes() so @observe()-decorated tool observations inherit it.
"""

from typing import Any, TypedDict

from langchain.agents import create_agent
from langfuse import propagate_attributes
from langfuse.langchain import CallbackHandler
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from backend.agent_engine.agents.config_loader import VersionConfig
from backend.agent_engine.tools import setup_tools
from backend.agent_engine.tools.registry import get_tools_by_names

_DEFAULT_SYSTEM_PROMPT = "You are FinLab-X, a strict, data-driven financial AI Agent."


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


class Orchestrator:
    """Version-agnostic Orchestrator that loads capabilities from config."""

    def __init__(self, config: VersionConfig):
        setup_tools()
        self.config = config
        self.tools = get_tools_by_names(config.tools)
        self.system_prompt = config.system_prompt or _DEFAULT_SYSTEM_PROMPT

        model = init_chat_model(config.model.name, temperature=config.model.temperature)
        tool_call_limit = ToolCallLimitMiddleware(
            run_limit=config.constraints.max_tool_calls_per_step,
        )
        self.agent = create_agent(
            model=model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            middleware=[tool_call_limit],
        )

    def run(self, prompt: str, **kwargs: object) -> OrchestratorResult:
        config, propagation = self._build_langfuse_config(**kwargs)
        with propagate_attributes(**propagation):
            result = self.agent.invoke(
                {"messages": [{"role": "user", "content": prompt}]},
                config=config,
            )
        return self._extract_result(result)

    async def arun(self, prompt: str, **kwargs: object) -> OrchestratorResult:
        """Execute the agent asynchronously (non-blocking).

        Use this from async FastAPI endpoints to avoid blocking the event loop.
        """
        config, propagation = self._build_langfuse_config(**kwargs)
        with propagate_attributes(**propagation):
            result = await self.agent.ainvoke(
                {"messages": [{"role": "user", "content": prompt}]},
                config=config,
            )
        return self._extract_result(result)

    def _build_langfuse_config(
        self,
        **kwargs: object,
    ) -> tuple[RunnableConfig, _LangfusePropagationAttributes]:
        handler = CallbackHandler()
        propagation: _LangfusePropagationAttributes = {}
        session_id = kwargs.get("session_id")
        if isinstance(session_id, str) and session_id:
            propagation["session_id"] = session_id
        return {"callbacks": [handler]}, propagation

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
