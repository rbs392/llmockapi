from pathlib import Path
import json
import yaml
import os
import sys
import aiohttp
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
    CliSettingsSource,
)
from pydantic import Field, AliasChoices


SYSTEM_PROMPT = """
You are an rest api server written in python.
The Api specs are defined below between <spec></spec> tags.
The expected response are defined between <responses></responses> tags.
Always return with following json structure {"content": any, "status_code": int, "headers": dict}.
<b>Never include backticks in your response.</b>
<b>Never respond anything outside of the specification.</b>
"""


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    api_key: str = Field(
        default="",
        validation_alias=AliasChoices("api_key", "api-key"),
    )
    base_url: str = Field(
        default="",
        validation_alias=AliasChoices("base_url", "base-url"),
    )
    mock_api_spec: str = Field(
        default="",
        validation_alias=AliasChoices("mock_api_spec", "mock-api-spec"),
    )

    model: str = Field(default="anthropic/claude-haiku-4.5")
    host: str = Field(default="localhost")
    port: int = Field(default=9000)

    _api_spec: str = ""
    _chat_template: str = ""

    @classmethod
    def settings_customise_sources(
        self,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Only parse CLI args if not in test mode (check if pytest is running)
        if "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST"):
            return env_settings, init_settings
        return CliSettingsSource(settings_cls, cli_parse_args=True), env_settings

    async def get_http_spec(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.mock_api_spec) as response:
                return await response.text()

    def get_local_spec(self):
        with open(self.mock_api_spec) as f:
            if self.mock_api_spec.endswith(".json"):
                return json.load(f)
            elif self.mock_api_spec.endswith(".yaml"):
                return yaml.safe_load(f)
            else:
                return f.read()

    async def get_api_spec(self):
        if self._api_spec:
            return self._api_spec

        if self.mock_api_spec.startswith("http"):
            self._api_spec = await self.get_http_spec()
            return self._api_spec

        self._api_spec = self.get_local_spec()
        return self._api_spec

    async def get_system_prompt(self):
        api_spec = await self.get_api_spec()
        return "\n".join(
            [
                SYSTEM_PROMPT,
                "",
                f"<spec>{api_spec}</spec>",
            ]
        )

    def get_chat_template(self):
        if self._chat_template == "":
            with open(Path(__file__).parent / "chat_template.html") as f:
                self._chat_template = f.read()
        return self._chat_template


config = Config()
