import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, mock_open, MagicMock
from llmockapi.config import Config, SYSTEM_PROMPT
from conftest import create_mock_aiohttp_session


@pytest.mark.unit
class TestConfig:
    """Test suite for Config class."""

    def test_config_initialization_with_defaults(self):
        """Test Config initialization with default values."""
        config = Config()
        assert config.api_key == ""
        assert config.base_url == ""
        assert config.mock_api_spec == ""
        assert config.model == "anthropic/claude-haiku-4.5"
        assert config.host == "localhost"
        assert config.port == 9000

    def test_config_initialization_with_custom_values(self):
        """Test Config initialization with custom values."""
        config = Config(
            api_key="test-key",
            base_url="https://test.com",
            mock_api_spec="./spec.json",
            model="test-model",
            host="0.0.0.0",
            port=8080,
        )
        assert config.api_key == "test-key"
        assert config.base_url == "https://test.com"
        assert config.mock_api_spec == "./spec.json"
        assert config.model == "test-model"
        assert config.host == "0.0.0.0"
        assert config.port == 8080

    def test_config_accepts_cli_args_format(self):
        """Test that Config accepts both underscore and hyphen formats."""
        config = Config(api_key="key1")
        assert config.api_key == "key1"

        config = Config(base_url="https://test.com")
        assert config.base_url == "https://test.com"

    @pytest.mark.asyncio
    async def test_get_http_spec(self, mock_config):
        """Test getting API spec from HTTP URL."""
        mock_config.mock_api_spec = "https://example.com/spec.json"
        test_spec = '{"swagger": "2.0", "info": {"title": "Test API"}}'

        mock_session = create_mock_aiohttp_session(test_spec)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await mock_config.get_http_spec()
            assert result == test_spec

    def test_get_local_spec_json(self, mock_config, api_spec_json):
        """Test getting local JSON API spec."""
        result = mock_config.get_local_spec()
        assert isinstance(result, dict)
        assert "swagger" in result
        assert result["swagger"] == "2.0"

    def test_get_local_spec_yaml(self, tmp_path):
        """Test getting local YAML API spec."""
        yaml_content = """
swagger: "2.0"
info:
  title: Test API
  version: 1.0.0
"""
        yaml_file = tmp_path / "spec.yaml"
        yaml_file.write_text(yaml_content)

        config = Config(
            api_key="test",
            base_url="https://test.com",
            mock_api_spec=str(yaml_file),
        )

        result = config.get_local_spec()
        assert isinstance(result, dict)
        assert result["swagger"] == "2.0"
        assert result["info"]["title"] == "Test API"

    def test_get_local_spec_plain_text(self, tmp_path):
        """Test getting local plain text spec."""
        text_content = "This is a plain text spec"
        text_file = tmp_path / "spec.txt"
        text_file.write_text(text_content)

        config = Config(
            api_key="test",
            base_url="https://test.com",
            mock_api_spec=str(text_file),
        )

        result = config.get_local_spec()
        assert result == text_content

    @pytest.mark.asyncio
    async def test_get_api_spec_caches_result(self, mock_config):
        """Test that get_api_spec caches the result."""
        # First call should load the spec
        result1 = await mock_config.get_api_spec()
        assert result1 is not None

        # Second call should return cached value
        result2 = await mock_config.get_api_spec()
        assert result2 == result1
        assert mock_config._api_spec == result1

    @pytest.mark.asyncio
    async def test_get_api_spec_http(self):
        """Test get_api_spec with HTTP URL."""
        config = Config(
            api_key="test",
            base_url="https://test.com",
            mock_api_spec="https://example.com/spec.json",
        )

        test_spec = '{"test": "spec"}'
        mock_session = create_mock_aiohttp_session(test_spec)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await config.get_api_spec()
            assert result == test_spec

    @pytest.mark.asyncio
    async def test_get_api_spec_local(self, mock_config, api_spec_json):
        """Test get_api_spec with local file."""
        result = await mock_config.get_api_spec()
        assert isinstance(result, dict)
        assert "swagger" in result

    @pytest.mark.asyncio
    async def test_get_system_prompt(self, mock_config):
        """Test system prompt generation."""
        system_prompt = await mock_config.get_system_prompt()

        assert SYSTEM_PROMPT in system_prompt
        assert "<spec>" in system_prompt
        assert "</spec>" in system_prompt

        # Should contain the API spec
        api_spec = await mock_config.get_api_spec()
        assert str(api_spec) in system_prompt

    def test_get_chat_template(self, mock_config):
        """Test getting chat template."""
        # Create a mock chat template file
        with patch("builtins.open", mock_open(read_data="<html>Chat Template</html>")):
            template = mock_config.get_chat_template()
            assert template == "<html>Chat Template</html>"

            # Second call should return cached value
            template2 = mock_config.get_chat_template()
            assert template2 == template

    def test_get_chat_template_caching(self, mock_config):
        """Test that chat template is cached."""
        with patch("builtins.open", mock_open(read_data="<html>Template</html>")):
            template1 = mock_config.get_chat_template()
            template2 = mock_config.get_chat_template()

            assert template1 == template2
            assert mock_config._chat_template == "<html>Template</html>"
