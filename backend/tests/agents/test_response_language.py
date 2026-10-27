import asyncio
from unittest.mock import MagicMock

import pytest
from langchain.agents.middleware.types import ModelRequest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from backend.agent_engine.agents.response_language import (
    ResponseLanguageMiddleware,
    detect_response_language,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Which export-control risks in NVIDIA's latest 10-K have materialized?",
            "English",
        ),
        ("微軟最近有什麼新聞？", "Traditional Chinese"),
        ("NVDA 的 10-K 提到哪些風險？", "Traditional Chinese"),
        ("AAPL 10-K", "English"),
    ],
)
def test_detect_response_language(text, expected):
    assert detect_response_language(text) == expected


def _request(messages, system_text="BASE PROMPT"):
    return ModelRequest(
        model=MagicMock(),
        messages=messages,
        system_message=SystemMessage(content=system_text),
        state={"messages": messages},
        runtime=MagicMock(),
    )


def _system_text(request: ModelRequest) -> str:
    return "".join(
        block["text"]
        for block in request.system_message.content_blocks
        if block["type"] == "text"
    )


def test_appends_language_of_latest_user_message_after_base_prompt():
    messages = [
        HumanMessage(content="微軟最近有什麼新聞？"),
        AIMessage(content="..."),
        HumanMessage(content="How does Microsoft's MD&A explain cloud growth?"),
        ToolMessage(content="10-K text " * 50, tool_call_id="t1"),
    ]
    seen = []

    ResponseLanguageMiddleware().wrap_model_call(_request(messages), seen.append)

    text = _system_text(seen[0])
    assert text.startswith("BASE PROMPT")
    assert "English" in text
    assert "Traditional Chinese" not in text


def test_async_path_matches_sync_path():
    messages = [HumanMessage(content="台積電最近有什麼重要新聞？")]
    seen = []

    async def handler(request):
        seen.append(request)

    asyncio.run(
        ResponseLanguageMiddleware().awrap_model_call(_request(messages), handler)
    )

    assert "Traditional Chinese" in _system_text(seen[0])


def test_leaves_request_untouched_without_a_user_message():
    request = _request([AIMessage(content="hi")])
    seen = []

    ResponseLanguageMiddleware().wrap_model_call(request, seen.append)

    assert seen[0] is request
