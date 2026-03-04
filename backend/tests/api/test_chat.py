"""Tests for chat API endpoint."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.api.main import app


client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_chat_endpoint_exists():
    """Test chat endpoint exists."""
    with patch("backend.api.routers.chat.Orchestrator") as mock_orch:
        with patch("backend.api.routers.chat.VersionConfigLoader") as mock_loader:
            mock_config = MagicMock()
            mock_config.name = "v1_baseline"
            mock_loader.return_value.load.return_value = mock_config

            mock_orch_instance = MagicMock()
            mock_orch_instance.run.return_value = {
                "response": "Test response",
                "tool_outputs": [],
                "version": "0.1.0",
            }
            mock_orch.return_value = mock_orch_instance

            response = client.post("/api/v1/chat", json={"message": "test"})
            assert response.status_code != 404
