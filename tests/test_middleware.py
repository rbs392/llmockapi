import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Response
from llmockapi.middleware import MockResponseMiddleWare
from llmockapi.config import Config


@pytest.mark.unit
class TestMockResponseMiddleWare:
    """Test suite for MockResponseMiddleWare class."""

    def test_middleware_initialization(self, mock_config):
        """Test middleware initialization."""
        middleware = MockResponseMiddleWare(config=mock_config)
        assert middleware.llm_client is not None
        assert middleware.llm_client.config == mock_config

    @pytest.mark.asyncio
    async def test_middleware_bypasses_internal_routes(self, mock_config):
        """Test that middleware bypasses /__internal routes."""
        middleware = MockResponseMiddleWare(config=mock_config)

        request = MagicMock(spec=Request)
        request.url.path = "/__internal/health"

        call_next = AsyncMock(return_value=Response(content="OK", status_code=200))

        response = await middleware(request, call_next)

        # Should call next handler
        call_next.assert_called_once_with(request)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_bypasses_favicon(self, mock_config):
        """Test that middleware bypasses /favicon.ico requests."""
        middleware = MockResponseMiddleWare(config=mock_config)

        request = MagicMock(spec=Request)
        request.url.path = "/favicon.ico"

        call_next = AsyncMock(return_value=Response(content="", status_code=404))

        response = await middleware(request, call_next)

        # Should call next handler
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_middleware_processes_api_routes(
        self, mock_config, mock_llm_response
    ):
        """Test that middleware processes regular API routes with LLM."""
        middleware = MockResponseMiddleWare(config=mock_config)

        request = MagicMock(spec=Request)
        request.url.path = "/pet/123"
        request.method = "GET"
        request.headers = {}
        request.body = AsyncMock(return_value=b"")
        request.state.messages = []

        call_next = AsyncMock()

        with patch.object(
            middleware.llm_client,
            "get_response",
            AsyncMock(return_value=Response(content='{"id": 123}', status_code=200)),
        ):
            response = await middleware(request, call_next)

            # Should NOT call next handler (bypassed by LLM)
            call_next.assert_not_called()

            # Should return LLM response
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_calls_llm_client_for_api_routes(self, mock_config):
        """Test that middleware calls LLM client for API routes."""
        middleware = MockResponseMiddleWare(config=mock_config)

        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        request.method = "POST"
        request.headers = {}
        request.body = AsyncMock(return_value=b'{"test": "data"}')
        request.state.messages = []

        call_next = AsyncMock()

        with patch.object(
            middleware.llm_client,
            "get_response",
            AsyncMock(return_value=Response(content="OK", status_code=200)),
        ) as mock_get_response:
            await middleware(request, call_next)

            # Should call LLM client
            mock_get_response.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_middleware_internal_path_variations(self, mock_config):
        """Test that middleware handles various internal path formats."""
        middleware = MockResponseMiddleWare(config=mock_config)
        call_next = AsyncMock(return_value=Response(content="OK", status_code=200))

        internal_paths = [
            "/__internal/health",
            "/__internal/messages",
            "/__internal/ui",
            "/__internal/some/deep/path",
        ]

        for path in internal_paths:
            request = MagicMock(spec=Request)
            request.url.path = path

            response = await middleware(request, call_next)

            # All internal paths should bypass to call_next
            assert call_next.called
            call_next.reset_mock()

    @pytest.mark.asyncio
    async def test_middleware_handles_different_http_methods(self, mock_config):
        """Test that middleware handles different HTTP methods."""
        middleware = MockResponseMiddleWare(config=mock_config)

        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]

        for method in methods:
            request = MagicMock(spec=Request)
            request.url.path = "/api/resource"
            request.method = method
            request.headers = {}
            request.body = AsyncMock(return_value=b"")
            request.state.messages = []

            call_next = AsyncMock()

            with patch.object(
                middleware.llm_client,
                "get_response",
                AsyncMock(return_value=Response(content="OK", status_code=200)),
            ):
                await middleware(request, call_next)

                # Should use LLM for all methods
                call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_middleware_preserves_request_state(self, mock_config):
        """Test that middleware preserves request state."""
        middleware = MockResponseMiddleWare(config=mock_config)

        request = MagicMock(spec=Request)
        request.url.path = "/pet/1"
        request.method = "GET"
        request.headers = {}
        request.body = AsyncMock(return_value=b"")
        request.state.messages = [{"role": "system", "content": "test"}]

        call_next = AsyncMock()

        with patch.object(
            middleware.llm_client,
            "get_response",
            AsyncMock(return_value=Response(content="OK", status_code=200)),
        ):
            await middleware(request, call_next)

            # State should be preserved
            assert len(request.state.messages) >= 1
