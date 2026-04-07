"""Tests for tool error sanitizer — removes secrets, paths, connection strings, stack traces."""


from backend.agent_engine.streaming.tool_error_sanitizer import sanitize_tool_error


class TestApiKeyRemoval:
    """API keys / tokens / secrets must be stripped."""

    def test_removes_bearer_token(self):
        raw = "Authorization failed: Bearer sk-abc123secretkey456"
        result = sanitize_tool_error(raw)
        assert "sk-abc123secretkey456" not in result
        assert "Authorization failed" in result

    def test_removes_api_key_parameter(self):
        raw = "Request to https://api.example.com?api_key=DEADBEEF123 failed: 403"
        result = sanitize_tool_error(raw)
        assert "DEADBEEF123" not in result

    def test_removes_openai_style_key(self):
        raw = "Error calling model with key sk-proj-abcdef1234567890abcdef"
        result = sanitize_tool_error(raw)
        assert "sk-proj-abcdef1234567890abcdef" not in result

    def test_removes_key_value_assignment(self):
        raw = "Config error: API_KEY=mysecretvalue123 is invalid"
        result = sanitize_tool_error(raw)
        assert "mysecretvalue123" not in result


class TestInternalPathRemoval:
    """Internal filesystem paths and hostnames must be removed."""

    def test_removes_unix_path(self):
        raw = "FileNotFoundError: /home/deploy/app/secrets/config.yaml not found"
        result = sanitize_tool_error(raw)
        assert "/home/deploy/app/secrets/config.yaml" not in result
        assert "FileNotFoundError" in result

    def test_removes_windows_path(self):
        raw = r"Error reading C:\Users\admin\AppData\credentials.json"
        result = sanitize_tool_error(raw)
        assert r"C:\Users\admin" not in result

    def test_removes_internal_hostname(self):
        raw = "ConnectionError: failed to reach db-primary.internal.corp:5432"
        result = sanitize_tool_error(raw)
        assert "db-primary.internal.corp" not in result
        assert "ConnectionError" in result


class TestConnectionStringRemoval:
    """Database connection strings with credentials must be cleared."""

    def test_removes_postgres_connection_string(self):
        raw = "OperationalError: could not connect to postgresql://user:pass@db.internal:5432/mydb"
        result = sanitize_tool_error(raw)
        assert "user:pass" not in result
        assert "db.internal" not in result

    def test_removes_redis_connection_string(self):
        raw = "RedisError: redis://secret:password@redis.host:6379/0 unreachable"
        result = sanitize_tool_error(raw)
        assert "secret:password" not in result

    def test_removes_mongodb_connection_string(self):
        raw = "MongoError: mongodb+srv://admin:p4ssw0rd@cluster.mongodb.net/db"
        result = sanitize_tool_error(raw)
        assert "admin:p4ssw0rd" not in result


class TestStackTraceStripping:
    """Multi-line stack traces should be reduced to the final description line."""

    def test_python_traceback_reduced_to_last_line(self):
        raw = (
            "Traceback (most recent call last):\n"
            '  File "/app/agent_engine/tools/yfinance.py", line 42, in fetch\n'
            "    response = session.get(url)\n"
            '  File "/app/.venv/lib/requests/api.py", line 75, in get\n'
            "    return request('GET', url)\n"
            "TimeoutError: yfinance API timeout after 30s"
        )
        result = sanitize_tool_error(raw)
        assert "yfinance API timeout" in result
        assert "Traceback" not in result
        assert "/app/agent_engine" not in result

    def test_multiline_error_without_traceback_preserved(self):
        raw = "Multiple issues found:\n- rate limit exceeded\n- retry after 60s"
        result = sanitize_tool_error(raw)
        assert "rate limit exceeded" in result


class TestNormalErrorsPreserved:
    """User-facing error descriptions must pass through unchanged."""

    def test_simple_timeout(self):
        raw = "yfinance API timeout"
        assert sanitize_tool_error(raw) == "yfinance API timeout"

    def test_rate_limit(self):
        raw = "Rate limit exceeded, please retry later"
        assert sanitize_tool_error(raw) == "Rate limit exceeded, please retry later"

    def test_not_found(self):
        raw = "Ticker INVALID not found"
        assert sanitize_tool_error(raw) == "Ticker INVALID not found"

    def test_empty_string(self):
        assert sanitize_tool_error("") == ""
