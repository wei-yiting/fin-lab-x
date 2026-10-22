"""Pin the answer language to the user's latest message on every model call.

A prompt rule like "answer in the user's language" is not enough once a turn
pulls tens of thousands of tokens of English 10-K text into context: the model
loses track of what the user wrote and answers in Chinese, Japanese, or Spanish.
This middleware decides the language in code and states it explicitly.
"""

import re
from collections.abc import Awaitable, Callable
from typing import Any, cast

from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ModelRequest, ModelResponse
from langchain_core.messages import HumanMessage, SystemMessage

_CJK_RE = re.compile(r"[㐀-鿿豈-﫿]")


def detect_response_language(text: str) -> str:
    """Return the language the final answer should be written in.

    The product serves English and Traditional Chinese users, so any Han
    character means Traditional Chinese; everything else is English.
    """
    return "Traditional Chinese" if _CJK_RE.search(text) else "English"


def _latest_user_text(request: ModelRequest) -> str | None:
    for message in reversed(request.messages):
        if isinstance(message, HumanMessage):
            return message.text
    return None


def _with_language_instruction(request: ModelRequest) -> ModelRequest:
    user_text = _latest_user_text(request)
    if user_text is None:
        return request
    language = detect_response_language(user_text)
    instruction = (
        f"\n\nRESPONSE LANGUAGE: The user's latest message is written in {language}. "
        f"Write your entire final answer in {language}, whatever language the tool "
        "outputs are in."
    )
    base_blocks = (
        request.system_message.content_blocks if request.system_message else []
    )
    new_system = SystemMessage(
        content=cast(
            "list[str | dict[str, str]]",
            [*base_blocks, {"type": "text", "text": instruction}],
        )
    )
    return request.override(system_message=new_system)


class ResponseLanguageMiddleware(AgentMiddleware):
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse[Any]],
    ) -> ModelResponse[Any]:
        return handler(_with_language_instruction(request))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse[Any]]],
    ) -> ModelResponse[Any]:
        return await handler(_with_language_instruction(request))
