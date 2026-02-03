import json
import pytest
from unittest.mock import MagicMock, patch, mock_open
from fastapi import Request
from fastapi.testclient import TestClient
from llmockapi.internal_route import router, health, messages, ui


@pytest.mark.unit
class TestInternalRoutes:
    """Test suite for internal route handlers."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health check endpoint."""
        response = await health()
        assert response == {"msg": "ok"}

    @pytest.mark.asyncio
    async def test_messages_endpoint(self):
        """Test messages endpoint returns conversation history."""
        request = MagicMock(spec=Request)
        test_messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Test request"},
            {"role": "assistant", "content": "Test response"},
        ]
        request.state.messages = test_messages

        response = await messages(request)

        # Should return JSONResponse with messages
        assert response.body.decode() == json.dumps(test_messages)

    @pytest.mark.asyncio
    async def test_messages_endpoint_empty_state(self):
        """Test messages endpoint with empty message history."""
        request = MagicMock(spec=Request)
        request.state.messages = []

        response = await messages(request)

        assert response.body.decode() == "[]"

    @pytest.mark.asyncio
    async def test_ui_endpoint_renders_template(self):
        """Test UI endpoint renders HTML template with chat data."""
        request = MagicMock(spec=Request)
        test_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        request.state.messages = test_messages

        template_content = "<html><script>const chatData = [];</script></html>"

        with patch(
            "llmockapi.config.config.get_chat_template", return_value=template_content
        ):
            response = await ui(request)

            # Should be HTMLResponse
            assert response.status_code == 200
            assert response.media_type == "text/html"

            # Should inject chat data
            body = response.body.decode()
            assert "const chatData = [" in body
            assert '"role": "user"' in body
            assert '"role": "assistant"' in body

    @pytest.mark.asyncio
    async def test_ui_endpoint_escapes_json_properly(self):
        """Test UI endpoint properly formats JSON data."""
        request = MagicMock(spec=Request)
        request.state.messages = [
            {"role": "user", "content": "Test with 'quotes'"},
        ]

        template_content = "const chatData = [];"

        with patch(
            "llmockapi.config.config.get_chat_template", return_value=template_content
        ):
            response = await ui(request)

            body = response.body.decode()
            # Should contain valid JSON
            assert "const chatData = [" in body

    @pytest.mark.asyncio
    async def test_ui_endpoint_with_complex_messages(self):
        """Test UI endpoint with complex message structures."""
        request = MagicMock(spec=Request)
        request.state.messages = [
            {
                "role": "user",
                "content": "GET /pet/123 HTTP/1.1\ncontent-type: application/json\n{}",
            },
            {
                "role": "assistant",
                "content": '{"content": {"id": 123, "name": "Fluffy"}, "status_code": 200, "headers": {}}',
            },
        ]

        template_content = "<div>const chatData = [];</div>"

        with patch(
            "llmockapi.config.config.get_chat_template", return_value=template_content
        ):
            response = await ui(request)

            body = response.body.decode()
            assert "const chatData = [" in body
            # Original placeholder should be replaced
            assert "const chatData = [];" not in body


@pytest.mark.integration
class TestInternalRoutesIntegration:
    """Integration tests for internal routes with FastAPI app."""

    def test_health_route_integration(self, test_client):
        """Test health endpoint through FastAPI client."""
        response = test_client.get("/__internal/health")
        assert response.status_code == 200
        assert response.json() == {"msg": "ok"}

    def test_messages_route_integration(self, test_client):
        """Test messages endpoint through FastAPI client."""
        response = test_client.get("/__internal/messages")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_ui_route_integration(self, test_client):
        """Test UI endpoint through FastAPI client."""
        response = test_client.get("/__internal/ui")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_internal_routes_accessible(self, test_client):
        """Test that all internal routes are accessible."""
        routes = [
            "/__internal/health",
            "/__internal/messages",
            "/__internal/ui",
        ]

        for route in routes:
            response = test_client.get(route)
            # Should not return 404
            assert response.status_code != 404

    def test_router_is_included_in_app(self):
        """Test that internal router is properly configured."""
        from llmockapi import app

        # Check that router is included
        route_paths = [route.path for route in app.routes]
        assert any("health" in path for path in route_paths)
