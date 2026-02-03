import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Response
from fastapi.datastructures import Headers
from llmockapi.client import LLMClient
from llmockapi.config import Config
from conftest import create_mock_aiohttp_session


@pytest.mark.unit
class TestLLMClient:
    """Test suite for LLMClient class."""

    def test_llm_client_initialization(self, mock_config):
        """Test LLMClient initialization."""
        client = LLMClient(config=mock_config)
        assert client.config == mock_config
        assert client.lock is not None

    def test_get_header_lines_filters_auth_headers(self, mock_config):
        """Test that get_header_lines filters out sensitive headers."""
        client = LLMClient(config=mock_config)
        headers = Headers(
            {
                "content-type": "application/json",
                "authorization": "Bearer secret-token",
                "basic": "secret-basic",
                "user-agent": "test-agent",
            }
        )

        header_lines = client.get_header_lines(headers)

        # Should include non-sensitive headers
        assert "content-type: application/json" in header_lines
        assert "user-agent: test-agent" in header_lines

        # Should exclude sensitive headers
        assert not any("authorization" in line.lower() for line in header_lines)
        assert not any("basic" in line.lower() for line in header_lines)

    def test_get_header_lines_empty_headers(self, mock_config):
        """Test get_header_lines with empty headers."""
        client = LLMClient(config=mock_config)
        headers = Headers({})
        header_lines = client.get_header_lines(headers)
        assert header_lines == []

    def test_sanitize_response_plain_json(self, mock_config, mock_llm_response):
        """Test sanitize_response with plain JSON response."""
        client = LLMClient(config=mock_config)
        result = client.sanitize_response(mock_llm_response)

        assert isinstance(result, dict)
        assert "content" in result
        assert "status_code" in result
        assert "headers" in result
        assert result["status_code"] == 200

    def test_sanitize_response_with_markdown_code_block(self, mock_config):
        """Test sanitize_response with JSON wrapped in markdown code blocks."""
        client = LLMClient(config=mock_config)

        response = {
            "choices": [
                {
                    "message": {
                        "content": '```json\n{"content": {"test": "data"}, "status_code": 200, "headers": {}}\n```'
                    }
                }
            ]
        }

        result = client.sanitize_response(response)

        assert isinstance(result, dict)
        assert result["content"]["test"] == "data"
        assert result["status_code"] == 200

    def test_sanitize_response_extracts_message_content(self, mock_config):
        """Test that sanitize_response correctly extracts message content."""
        client = LLMClient(config=mock_config)

        response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "content": {"id": 1, "name": "test"},
                                "status_code": 201,
                                "headers": {"content-type": "application/json"},
                            }
                        )
                    }
                }
            ]
        }

        result = client.sanitize_response(response)

        assert result["content"]["id"] == 1
        assert result["content"]["name"] == "test"
        assert result["status_code"] == 201

    @pytest.mark.asyncio
    async def test_get_response_constructs_proper_request_format(
        self, mock_config, mock_request, mock_llm_response
    ):
        """Test that get_response constructs the request in proper HTTP format."""
        client = LLMClient(config=mock_config)

        # Create properly mocked aiohttp session
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value=mock_llm_response)

        mock_post_ctx = AsyncMock()
        mock_post_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_post_ctx)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            response = await client.get_response(mock_request)

            # Verify the message was added to state
            assert len(mock_request.state.messages) == 2  # user + assistant
            user_message = mock_request.state.messages[0]

            # Verify proper HTTP format
            assert user_message["role"] == "user"
            assert "GET /pet/123 HTTP/1.1" in user_message["content"]
            assert "content-type: application/json" in user_message["content"]

    @pytest.mark.asyncio
    async def test_get_response_sends_to_llm_api(
        self, mock_config, mock_request, mock_llm_response
    ):
        """Test that get_response sends request to LLM API."""
        client = LLMClient(config=mock_config)

        mock_session = create_mock_aiohttp_session(mock_llm_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            await client.get_response(mock_request)

            # Verify API was called
            mock_session.post.assert_called_once()
            call_args = mock_session.post.call_args

            # Verify correct endpoint
            assert call_args[0][0] == "v1/chat/completions"

            # Verify payload structure
            payload = json.loads(call_args[1]["data"])
            assert payload["model"] == mock_config.model
            assert "messages" in payload

    @pytest.mark.asyncio
    async def test_get_response_returns_fastapi_response(
        self, mock_config, mock_request, mock_llm_response
    ):
        """Test that get_response returns a proper FastAPI Response."""
        client = LLMClient(config=mock_config)

        mock_session = create_mock_aiohttp_session(mock_llm_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            response = await client.get_response(mock_request)

            assert isinstance(response, Response)
            assert response.status_code == 200
            assert "content-type" in response.headers

    @pytest.mark.asyncio
    async def test_get_response_uses_lock(
        self, mock_config, mock_request, mock_llm_response
    ):
        """Test that get_response uses asyncio lock."""
        client = LLMClient(config=mock_config)

        mock_session = create_mock_aiohttp_session(mock_llm_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with patch.object(
                client.lock, "acquire", wraps=client.lock.acquire
            ) as mock_acquire:
                await client.get_response(mock_request)
                mock_acquire.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_response_includes_request_body(
        self, mock_config, mock_llm_response
    ):
        """Test that get_response includes request body in the message."""
        client = LLMClient(config=mock_config)

        request = MagicMock(spec=Request)
        request.method = "POST"
        request.url.path = "/pet"
        request.headers = Headers({"content-type": "application/json"})
        request.body = AsyncMock(
            return_value=b'{"name": "Fluffy", "status": "available"}'
        )
        request.state.messages = []

        mock_session = create_mock_aiohttp_session(mock_llm_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            await client.get_response(request)

            user_message = request.state.messages[0]
            assert (
                '{"name": "Fluffy", "status": "available"}' in user_message["content"]
            )

    @pytest.mark.asyncio
    async def test_get_response_stores_conversation_history(
        self, mock_config, mock_request, mock_llm_response
    ):
        """Test that get_response stores both user and assistant messages."""
        client = LLMClient(config=mock_config)

        mock_session = create_mock_aiohttp_session(mock_llm_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            await client.get_response(mock_request)

            # Should have user message and assistant message
            assert len(mock_request.state.messages) == 2
            assert mock_request.state.messages[0]["role"] == "user"
            assert mock_request.state.messages[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_get_response_with_custom_headers(
        self, mock_config, mock_llm_response
    ):
        """Test get_response includes custom headers in LLM request."""
        client = LLMClient(config=mock_config)

        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url.path = "/test"
        request.headers = Headers({"x-custom-header": "custom-value"})
        request.body = AsyncMock(return_value=b"")
        request.state.messages = []

        mock_session = create_mock_aiohttp_session(mock_llm_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            await client.get_response(request)

            user_message = request.state.messages[0]
            assert "x-custom-header: custom-value" in user_message["content"]
