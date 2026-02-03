from typing import Callable

from fastapi import Request

from llmockapi.client import LLMClient
from llmockapi.config import Config


class MockResponseMiddleWare:
    def __init__(self, config: Config):
        self.llm_client = LLMClient(config=config)

    async def __call__(self, request: Request, call_next: Callable):
        if request.url.path.startswith("/favicon.ico"):
            return await call_next(request)
        if request.url.path.startswith("/__internal"):
            return await call_next(request)
        return await self.llm_client.get_response(request)
