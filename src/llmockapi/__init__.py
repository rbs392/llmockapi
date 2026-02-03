from fastapi.concurrency import asynccontextmanager
import uvicorn
from fastapi import FastAPI

from llmockapi.config import Config, config
from llmockapi.middleware import MockResponseMiddleWare
from llmockapi.internal_route import router as internal_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield {
        "messages": [
            {
                "role": "system",
                "content": await config.get_system_prompt(),
            }
        ]
    }


app = FastAPI(
    root_path="/__internal",
    lifespan=lifespan,
)
app.include_router(internal_router)
app.middleware("http")(MockResponseMiddleWare(config=config))


def main(config: Config = config) -> None:
    uvicorn.run(
        "llmockapi:app",
        host=config.host,
        port=config.port,
        reload=True,
    )
