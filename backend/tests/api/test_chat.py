"""Tests for streaming chat API endpoint."""

from unittest.mock import MagicMock


from backend.api.main import app
from backend.api.routers.chat import get_orchestrator, _active_sessions
from backend.agent_engine.streaming.domain_events_schema import (
    Finish,
    MessageStart,
    TextDelta,
    TextEnd,
    TextStart,
    Usage,
)

# --- helpers ---

def _msg(role: str, text: str, msg_id: str = "m1") -> dict:
    return {"id": msg_id, "role": role, "parts": [{"type": "text", "text": text}]}


def _make_mock_orchestrator():
    mock = MagicMock()

    async def _astream_run(**kwargs):
        yield MessageStart(message_id="msg-1", session_id=kwargs["session_id"])
        yield TextStart(text_id="t-1")
        yield TextDelta(text_id="t-1", delta="Hello")
        yield TextEnd(text_id="t-1")
        yield Finish(finish_reason="stop", usage=Usage())

    mock.astream_run = _astream_run
    return mock


def _override_orchestrator(mock_orchestrator):
    app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator


def _clear_overrides():
    app.dependency_overrides.clear()
    _active_sessions.clear()


# --- happy path ---

class TestStreamChatHappyPath:
    def test_returns_200_with_sse_content_type(self, client):
        _override_orchestrator(_make_mock_orchestrator())
        try:
            response = client.post(
                "/api/v1/chat",
                json={"id": "s1", "messages": [_msg("user", "hi")], "trigger": "submit-message"},
            )
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
        finally:
            _clear_overrides()

    def test_returns_vercel_ai_header(self, client):
        _override_orchestrator(_make_mock_orchestrator())
        try:
            response = client.post(
                "/api/v1/chat",
                json={"id": "s1", "messages": [_msg("user", "hi")], "trigger": "submit-message"},
            )
            assert response.headers["x-vercel-ai-ui-message-stream"] == "v1"
        finally:
            _clear_overrides()

    def test_response_body_contains_sse_data(self, client):
        _override_orchestrator(_make_mock_orchestrator())
        try:
            response = client.post(
                "/api/v1/chat",
                json={"id": "s1", "messages": [_msg("user", "hi")], "trigger": "submit-message"},
            )
            body = response.text
            assert "data: " in body
            assert '"type": "start"' in body
            assert '"type": "text-start"' in body
            assert '"type": "text-delta"' in body
            assert '"type": "finish"' in body
        finally:
            _clear_overrides()


# --- validation ---

class TestStreamChatValidation:
    def test_id_empty_string_returns_422(self, client):
        response = client.post(
            "/api/v1/chat",
            json={"id": "", "messages": [_msg("user", "hi")], "trigger": "submit-message"},
        )
        assert response.status_code == 422

    def test_id_missing_returns_422(self, client):
        response = client.post(
            "/api/v1/chat",
            json={"messages": [_msg("user", "hi")], "trigger": "submit-message"},
        )
        assert response.status_code == 422

    def test_submit_with_no_user_message_returns_422(self, client):
        response = client.post(
            "/api/v1/chat",
            json={"id": "s1", "messages": [_msg("assistant", "hi")], "trigger": "submit-message"},
        )
        assert response.status_code == 422

    def test_empty_messages_submit_returns_422(self, client):
        response = client.post(
            "/api/v1/chat",
            json={"id": "s1", "messages": [], "trigger": "submit-message"},
        )
        assert response.status_code == 422

    def test_regenerate_missing_message_id_returns_422(self, client):
        response = client.post(
            "/api/v1/chat",
            json={"id": "s1", "messages": [], "trigger": "regenerate-message"},
        )
        assert response.status_code == 422

    def test_missing_trigger_returns_422(self, client):
        response = client.post(
            "/api/v1/chat",
            json={"id": "s1", "messages": [_msg("user", "hi")]},
        )
        assert response.status_code == 422

    def test_missing_messages_returns_422(self, client):
        response = client.post(
            "/api/v1/chat",
            json={"id": "s1", "trigger": "submit-message"},
        )
        assert response.status_code == 422


# --- AI SDK v6 specific ---

class TestStreamChatAiSdkV6Format:
    def test_submit_message_extracts_last_user_text(self, client):
        """確認 validator 從 messages 陣列中正確提取最後一個 user message 的文字。"""
        captured = {}

        mock = MagicMock()

        async def _astream_run(**kwargs):
            captured["message"] = kwargs["message"]
            captured["trigger"] = kwargs["trigger"]
            yield MessageStart(message_id="msg-1", session_id=kwargs["session_id"])
            yield TextStart(text_id="t-1")
            yield TextDelta(text_id="t-1", delta="ok")
            yield TextEnd(text_id="t-1")
            yield Finish(finish_reason="stop", usage=Usage())

        mock.astream_run = _astream_run
        _override_orchestrator(mock)

        try:
            response = client.post(
                "/api/v1/chat",
                json={
                    "id": "s1",
                    "messages": [
                        _msg("user", "first question", "m1"),
                        _msg("assistant", "answer", "m2"),
                        _msg("user", "follow-up question", "m3"),
                    ],
                    "trigger": "submit-message",
                },
            )
            assert response.status_code == 200
            assert captured["message"] == "follow-up question"
            assert captured["trigger"] is None
        finally:
            _clear_overrides()

    def test_regenerate_message_trigger_is_normalized(self, client):
        """確認 trigger: regenerate-message 被正規化為 regenerate 傳給 orchestrator。"""
        captured = {}

        mock = MagicMock()

        async def _validate_regenerate(**kwargs):
            pass

        async def _astream_run(**kwargs):
            captured["trigger"] = kwargs["trigger"]
            yield MessageStart(message_id="msg-1", session_id=kwargs["session_id"])
            yield TextStart(text_id="t-1")
            yield TextDelta(text_id="t-1", delta="ok")
            yield TextEnd(text_id="t-1")
            yield Finish(finish_reason="stop", usage=Usage())

        mock.astream_run = _astream_run
        mock.validate_regenerate = _validate_regenerate
        _override_orchestrator(mock)

        try:
            response = client.post(
                "/api/v1/chat",
                json={
                    "id": "s1",
                    "messages": [],
                    "trigger": "regenerate-message",
                    "messageId": "msg-to-regen",
                },
            )
            assert response.status_code == 200
            assert captured["trigger"] == "regenerate"
        finally:
            _clear_overrides()


# --- session lock ---

class TestStreamChatSessionLock:
    def test_concurrent_request_returns_409(self, client):
        session_id = "locked-session"
        _active_sessions.add(session_id)
        _override_orchestrator(_make_mock_orchestrator())

        try:
            response = client.post(
                "/api/v1/chat",
                json={"id": session_id, "messages": [_msg("user", "hi")], "trigger": "submit-message"},
            )
            assert response.status_code == 409
            assert response.json()["detail"] == "Session busy"
        finally:
            _clear_overrides()


# --- orchestrator error ---

class TestStreamChatOrchestratorError:
    def test_value_error_yields_sse_error_events(self, client):
        mock_orch = MagicMock()

        async def _error_stream(**kwargs):
            raise ValueError("messageId does not match")
            yield  # make it a generator  # noqa: RUF027

        mock_orch.astream_run = _error_stream
        _override_orchestrator(mock_orch)

        try:
            response = client.post(
                "/api/v1/chat",
                json={"id": "s1", "messages": [_msg("user", "hi")], "trigger": "submit-message"},
            )
            assert response.status_code == 200
            body = response.text
            assert '"type": "error"' in body
            assert "messageId does not match" in body
            assert '"type": "finish"' in body
            assert '"finishReason": "error"' in body
        finally:
            _clear_overrides()


class TestRenamedInvokeEndpoint:
    def test_chat_invoke_still_works(self, client):
        from unittest.mock import AsyncMock
        from backend.api.routers.chat_invoke import get_orchestrator as get_invoke_orch

        mock = MagicMock()
        mock.arun = AsyncMock(
            return_value={
                "response": "ok",
                "tool_outputs": [],
                "model": "test",
                "version": "0.1.0",
            }
        )
        app.dependency_overrides[get_invoke_orch] = lambda: mock
        try:
            response = client.post(
                "/api/v1/chat/invoke", json={"message": "test"}
            )
            assert response.status_code == 200
            assert response.json()["response"] == "ok"
        finally:
            app.dependency_overrides.clear()
