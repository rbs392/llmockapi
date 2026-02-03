import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request
from llmockapi.config import Config


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
    return TestClient(test_app)
