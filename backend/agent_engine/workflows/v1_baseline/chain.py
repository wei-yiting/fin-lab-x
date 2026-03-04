from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from backend.agent_engine.agents.specialized.tools import V1_BASELINE_TOOLS
from backend.agent_engine.workflows.v1_baseline.prompts import SYSTEM_PROMPT


@dataclass(frozen=True)
class NaiveChainDebug:
    response: str
    tool_calls: list[dict[str, Any]]
    tool_outputs: list[dict[str, Any]]


@dataclass(frozen=True)
class NaiveChain:
    prompt: ChatPromptTemplate
    model: BaseChatModel
    tools: Sequence[Any]
    output_parser: StrOutputParser

    def invoke(self, user_input: str) -> str:
        debug = self.invoke_with_debug(user_input)
        return debug.response

    def invoke_with_debug(self, user_input: str) -> NaiveChainDebug:
        messages = self.prompt.format_messages(user_input=user_input)
        model_with_tools = self.model.bind_tools(self.tools)
        initial_response = model_with_tools.invoke(messages)
        tool_calls = _normalize_tool_calls(initial_response)
        tool_outputs: list[dict[str, Any]] = []

        if tool_calls:
            tool_messages = _execute_tool_calls(self.tools, tool_calls, tool_outputs)
            final_messages = list(messages) + [initial_response] + tool_messages
            final_response = self.model.invoke(final_messages)
        else:
            final_response = initial_response

        response_text = self.output_parser.invoke(final_response)
        return NaiveChainDebug(
            response=response_text,
            tool_calls=tool_calls,
            tool_outputs=tool_outputs,
        )


def _normalize_tool_calls(message: BaseMessage) -> list[dict[str, Any]]:
    raw_calls = getattr(message, "tool_calls", None)
    if not raw_calls:
        return []

    normalized: list[dict[str, Any]] = []
    for call in raw_calls:
        if isinstance(call, dict):
            normalized.append(
                {
                    "id": call.get("id"),
                    "name": call.get("name"),
                    "args": call.get("args", {}),
                }
            )
        else:
            normalized.append(
                {
                    "id": getattr(call, "id", None),
                    "name": getattr(call, "name", None),
                    "args": getattr(call, "args", {}),
                }
            )
    return normalized


def _execute_tool_calls(
    tools: Sequence[Any],
    tool_calls: Iterable[dict[str, Any]],
    tool_outputs: list[dict[str, Any]],
) -> list[ToolMessage]:
    tool_map = {tool.name: tool for tool in tools}
    tool_messages: list[ToolMessage] = []

    for call in tool_calls:
        tool_name = call.get("name")
        tool_args = call.get("args", {})
        tool = tool_map.get(tool_name)
        if tool is None:
            result: Any = f"Error: Tool '{tool_name}' is not available."
        else:
            try:
                result = tool.invoke(tool_args)
            except Exception as exc:
                result = f"Error: Tool '{tool_name}' failed: {exc}"

        tool_outputs.append(
            {
                "name": tool_name,
                "args": tool_args,
                "result": result,
            }
        )
        tool_messages.append(
            ToolMessage(content=str(result), tool_call_id=call.get("id"))
        )

    return tool_messages


def create_naive_chain(
    model_name: str | None = None, temperature: float = 0.0
) -> NaiveChain:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{user_input}"),
        ]
    )
    resolved_model = model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    model = ChatOpenAI(model=resolved_model, temperature=temperature)
    output_parser = StrOutputParser()
    return NaiveChain(
        prompt=prompt,
        model=model,
        tools=V1_BASELINE_TOOLS,
        output_parser=output_parser,
    )
