import asyncio
from llmockapi.config import config
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi import APIRouter, Request
import json


router = APIRouter()


@router.get("/health")
async def health():
    return {"msg": "ok"}


@router.get("/messages")
async def messages(request: Request):
    return JSONResponse(
        content=request.state.messages,
    )


@router.get("/ui")
async def ui(request: Request):
    async with asyncio.Lock():
        template = config.get_chat_template()
        messages = json.dumps(request.state.messages, default=str)

        return HTMLResponse(
            content=template.replace(
                "const chatData = [];",
                f"const chatData = {messages};",
            )
        )
