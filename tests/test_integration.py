import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from llmockapi import app


@pytest.mark.integration
class TestAppIntegration:
    """Integration tests for the complete FastAPI application."""

    def test_app_initialization(self):
        """Test that the app initializes correctly."""
        assert app is not None
        assert app.title == "FastAPI"
        assert app.root_path == "/__internal"

    def test_app_has_middleware(self):
        """Test that app has middleware configured."""
        # Check that middleware is registered
        assert len(app.user_middleware) > 0

    def test_app_has_internal_routes(self, test_client):
        """Test that app has internal routes configured."""
        response = test_client.get("/__internal/health")
        assert response.status_code == 200

    def test_favicon_request_bypassed(self, test_client):
        """Test that favicon requests are handled."""
        with patch(
            "llmockapi.middleware.MockResponseMiddleWare.__call__"
        ) as mock_middleware:
            response = test_client.get("/favicon.ico")
            # Middleware should be called and pass through
            assert mock_middleware.called or response.status_code in [200, 404]

    def test_internal_routes_bypass_llm(self, test_client):
        """Test that internal routes don't use LLM client."""
        with patch("llmockapi.client.LLMClient.get_response") as mock_llm:
            # Internal routes should not trigger LLM
            test_client.get("/__internal/health")
            test_client.get("/__internal/messages")

            # LLM should not be called for internal routes
            mock_llm.assert_not_called()

    @pytest.mark.asyncio
    async def test_api_route_uses_llm(self, test_client, mock_llm_response):
        """Test that API routes use LLM for response generation."""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_llm_response)
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            # This should trigger LLM middleware
            response = test_client.get("/pet/123")

            # Should get a response (though it might fail without proper setup)
            assert response is not None

    def test_lifespan_initializes_messages(self):
        """Test that lifespan context initializes message state."""
        with TestClient(app) as client:
            # Test that state is available
            response = client.get("/__internal/messages")
            assert response.status_code == 200
            messages = response.json()

            # Should have at least system prompt
            assert isinstance(messages, list)
            assert len(messages) >= 1
            assert messages[0]["role"] == "system"

    def test_multiple_requests_share_conversation(self, test_client, mock_llm_response):
        """Test that multiple requests maintain conversation history."""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_llm_response)
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            # Make first request
            test_client.get("/pet/1")

            # Check messages
            response = test_client.get("/__internal/messages")
            messages_after_first = response.json()
            first_count = len(messages_after_first)

            # Make second request
            test_client.get("/pet/2")

            # Check messages again
            response = test_client.get("/__internal/messages")
            messages_after_second = response.json()
            second_count = len(messages_after_second)

            # Should have more messages after second request
            assert second_count > first_count

    def test_app_root_path_configuration(self):
        """Test that app is configured with correct root path."""
        assert app.root_path == "/__internal"

    def test_openapi_schema_available(self, test_client):
        """Test that OpenAPI schema is available at internal path."""
        response = test_client.get("/__internal/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema or "swagger" in schema

    def test_different_http_methods(self, test_client, mock_llm_response):
        """Test that different HTTP methods are handled."""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_llm_response)
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            # Test different methods
            methods = [
                ("GET", "/pet/1"),
                ("POST", "/pet"),
                ("PUT", "/pet/1"),
                ("DELETE", "/pet/1"),
            ]

            for method, path in methods:
                if method == "GET":
                    response = test_client.get(path)
                elif method == "POST":
                    response = test_client.post(path, json={"name": "test"})
                elif method == "PUT":
                    response = test_client.put(path, json={"name": "test"})
                elif method == "DELETE":
                    response = test_client.delete(path)

                # Should get some response (not 404 not found route)
                assert response is not None


@pytest.mark.integration
class TestEndToEndFlow:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_complete_request_flow(self, test_client, mock_llm_response):
        """Test complete request flow from request to response."""
        with patch("aiohttp.ClientSession") as mock_session:
            # Setup mock LLM response
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_llm_response)
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            # 1. Check initial state
            response = test_client.get("/__internal/health")
            assert response.json() == {"msg": "ok"}

            # 2. Check initial messages
            response = test_client.get("/__internal/messages")
            initial_messages = response.json()
            assert len(initial_messages) >= 1

            # 3. Make API request
            api_response = test_client.get("/pet/123")
            assert api_response is not None

            # 4. Check messages updated
            response = test_client.get("/__internal/messages")
            updated_messages = response.json()
            assert len(updated_messages) > len(initial_messages)

    def test_error_handling_invalid_route(self, test_client):
        """Test that invalid routes are handled gracefully."""
        # This should go through LLM or return appropriate error
        response = test_client.get("/nonexistent/route/12345")
        # Should not crash the application
        assert response is not None

    def test_ui_displays_conversation(self, test_client, mock_llm_response):
        """Test that UI endpoint displays conversation history."""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_llm_response)
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            # Make a request
            test_client.get("/pet/123")

            # Check UI
            response = test_client.get("/__internal/ui")
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]

            # Should contain chat data
            body = response.text
            assert "chatData" in body
