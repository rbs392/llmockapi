import os
import logging
import json
import aiohttp
import asyncio
from fastapi.datastructures import Headers
from fastapi import Request, Response

from llmockapi.config import Config

logging.basicConfig(
    level=logging.getLevelName(os.getenv("LOG_LEVEL", "INFO")),
)
logger = logging.getLogger("LLMClient")


class LLMClient:
    def __init__(self, config: Config):
        self.config = config
        self.lock = asyncio.Lock()

    def get_header_lines(self, headers: Headers):
        return [
            f"{key}: {value}"
            for key, value in headers.items()
            if key.lower() not in ["authorization", "basic"]
        ]

    def sanitize_response(self, json_response: dict):
        logger.debug(json_response)
        message: str = json_response["choices"][0]["message"]["content"]
        if message.startswith("```"):
            message = message.replace("```json\n", "")
            message = message.replace("\n```", "")
        logger.debug(message)
        return json.loads(message)

    async def get_response(self, request: Request):
        async with self.lock:
            body = await request.body()
            request.state.messages.append(
                {
                    "role": "user",
                    "content": "\r\n".join(
                        [
                            f"{request.method} {request.url.path} HTTP/1.1",
                            *self.get_header_lines(request.headers),
                            body.decode(),
                        ]
                    ),
                }
            )
            payload = {
                "model": self.config.model,
                "messages": request.state.messages,
            }

            logger.debug(payload)

            async with aiohttp.ClientSession(
                base_url=self.config.base_url.strip("/") + "/",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "content-type": "application/json",
                },
            ) as session:
                async with session.post(
                    "v1/chat/completions",
                    data=json.dumps(payload),
                ) as res:
                    response = self.sanitize_response(await res.json())
                    request.state.messages.append(
                        {"role": "assistant", "content": json.dumps(response)}
                    )
                    return Response(
                        status_code=response["status_code"],
                        content=json.dumps(response["content"], default=str),
                        headers=response["headers"],
                    )
