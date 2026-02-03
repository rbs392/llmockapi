import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request
from llmockapi.config import Config


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    """Isolate environment variables for each test."""
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("BASE_URL", raising=False)
    monkeypatch.delenv("MOCK_API_SPEC", raising=False)
    monkeypatch.delenv("MODEL", raising=False)
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = Config(
        api_key="test-api-key",
        base_url="https://api.test.com",
        mock_api_spec=str(Path(__file__).parent / "mocks" / "api_specs.json"),
        model="test-model",
        host="localhost",
        port=9000,
    )
    return config


@pytest.fixture
def api_spec_json():
    """Load the test API specification."""
    spec_path = Path(__file__).parent / "mocks" / "api_specs.json"
    with open(spec_path) as f:
        return json.load(f)


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request."""
    request = MagicMock(spec=Request)
    request.method = "GET"
    request.url.path = "/pet/123"
    request.headers = {"content-type": "application/json"}
    request.body = AsyncMock(return_value=b'{"test": "data"}')
    request.state.messages = []
    return request


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "content": {
                                "id": 123,
                                "name": "Fluffy",
                                "status": "available",
                            },
                            "status_code": 200,
                            "headers": {"content-type": "application/json"},
                        }
                    )
                }
            }
        ]
    }


@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    from llmockapi import app

    return app


@pytest.fixture
def test_client(test_app):
    """Create a test client for the FastAPI application."""
    with TestClient(test_app) as client:
        yield client


def create_mock_aiohttp_session(response_data):
    """Helper to create a properly mocked aiohttp session."""
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value=response_data)
    mock_response.text = AsyncMock(
        return_value=json.dumps(response_data)
        if isinstance(response_data, dict)
        else response_data
    )

    mock_post_ctx = AsyncMock()
    mock_post_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post_ctx.__aexit__ = AsyncMock(return_value=None)

    mock_get_ctx = AsyncMock()
    mock_get_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_get_ctx.__aexit__ = AsyncMock(return_value=None)

    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_post_ctx)
    mock_session.get = MagicMock(return_value=mock_get_ctx)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    return mock_session
