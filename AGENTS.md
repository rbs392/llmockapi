# Agent Guidelines for llmockapi

This document provides coding standards and development guidelines for AI agents working on the llmockapi codebase.

## Project Overview

llmockapi is a Python-based FastAPI application that uses LLMs to dynamically generate mock API responses based on OpenAPI/Swagger specifications. The codebase is intentionally minimal (~269 LOC) with a focus on simplicity and clarity.

## Build, Test, and Lint Commands

### Package Management
- **Package Manager**: `uv` (modern Python package manager)
- **Install dependencies**: `pip install -e .`
- **Install with test dependencies**: `pip install -e ".[test]"`

### Running the Application
```bash
# Using CLI command
llmockapi

# Using Python module
python -m llmockapi

# With CLI arguments
llmockapi --api-key KEY --base-url URL --mock-api-spec PATH
```

### Testing
**Note**: No test framework is currently configured or running. Test dependencies are defined (pytest, pytest-asyncio, pytest-cov, httpx, pytest-mock) but no test suite exists yet.

- **Do NOT attempt to run tests** - there are no test files to execute
- When adding tests in the future, use: `pytest tests/`
- For single test: `pytest tests/test_file.py::test_function_name`

### Linting and Formatting
**Note**: No linting or formatting tools are configured. Follow the code style patterns observed in existing code.

- **No linter configured** (no ruff, flake8, pylint, etc.)
- **No formatter configured** (no black, ruff format, etc.)
- **No type checker configured** (no mypy, pyright, etc.)
- **No pre-commit hooks** configured

## Code Style Guidelines

### Python Version
- **Minimum**: Python 3.12
- **Current Runtime**: Python 3.14.2
- Use modern Python 3.12+ features when appropriate

### Imports
**Import Order** (follow standard Python conventions):
1. Standard library imports
2. Third-party imports (FastAPI, aiohttp, etc.)
3. Local application imports

**Example**:
```python
import os
import logging
import json

import aiohttp
import asyncio
from fastapi import Request, Response
from fastapi.datastructures import Headers

from llmockapi.config import Config
```

**Import Style**:
- Use absolute imports: `from llmockapi.config import Config`
- Group related imports: `from fastapi import Request, Response`
- Avoid wildcard imports: `from module import *`

### Formatting

**Indentation**: 4 spaces (never tabs)

**Line Length**: No strict limit enforced, but keep lines reasonable (~100 chars)

**Whitespace**:
- Trim trailing whitespace (enforced by .editorconfig)
- Insert final newline in all files (enforced by .editorconfig)

**Strings**: Use double quotes `"` for strings (observed pattern in codebase)

**JSON Files**: 2-space indentation (enforced by .editorconfig)

### Type Hints
**Coverage**: Type hints are encouraged but not comprehensive
- Add type hints to function signatures
- Use built-in types when possible: `dict`, `list`, `str`, `int`
- Use Pydantic models for structured data
- Return types should be specified

**Example**:
```python
def get_header_lines(self, headers: Headers) -> list[str]:
    return [f"{key}: {value}" for key, value in headers.items()]

async def get_response(self, request: Request) -> Response:
    # implementation
```

### Naming Conventions

**Files**: `snake_case.py`
- `client.py`, `config.py`, `middleware.py`

**Classes**: `PascalCase`
- `LLMClient`, `Config`, `MockResponseMiddleWare`

**Functions/Methods**: `snake_case`
- `get_response()`, `sanitize_response()`, `get_header_lines()`

**Variables**: `snake_case`
- `api_key`, `base_url`, `request_body`

**Constants**: `UPPER_SNAKE_CASE`
- `SYSTEM_PROMPT`, `LOG_LEVEL`

**Private Attributes**: Prefix with underscore
- `_api_spec`, `_chat_template`

### Async/Await
**Critical**: This is an async application. All I/O operations must be async.

```python
# Use async/await for all I/O
async def get_response(self, request: Request):
    body = await request.body()
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as res:
            response = await res.json()
```

**Patterns**:
- Use `asyncio.Lock()` for thread safety when needed
- Use `async with` for context managers
- All HTTP calls must be async (use `aiohttp`, not `requests`)
- FastAPI routes automatically support async

### Error Handling
**Current State**: Minimal error handling in codebase

**Guidelines**:
- Let FastAPI handle HTTP errors naturally
- Log errors using Python's `logging` module
- Don't add excessive try/except blocks unless necessary
- Use appropriate HTTP status codes in responses

### Logging
**Configuration**:
```python
import logging
import os

logging.basicConfig(
    level=logging.getLevelName(os.getenv("LOG_LEVEL", "INFO")),
)
logger = logging.getLogger("ModuleName")
```

**Usage**:
- `logger.debug()` for detailed debugging information
- `logger.info()` for general informational messages
- `logger.warning()` for warnings
- `logger.error()` for errors

### Configuration Management
**Use Pydantic Settings** for all configuration:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices

class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    api_key: str = Field(
        default="",
        validation_alias=AliasChoices("api_key", "api-key"),
    )
```

**Support both underscore and hyphen** in CLI args: `api_key` and `api-key`

## Framework-Specific Patterns

### FastAPI
**Lifespan Management**: Use for initialization
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield {"messages": [system_prompt]}

app = FastAPI(lifespan=lifespan)
```

**State Management**: Store request-specific data in `request.state`
```python
request.state.messages.append(message)
```

**Middleware**: Use class-based middleware
```python
class MockResponseMiddleWare:
    async def __call__(self, request: Request, call_next: Callable):
        if request.url.path.startswith("/__internal"):
            return await call_next(request)
        return await self.llm_client.get_response(request)

app.middleware("http")(MockResponseMiddleWare(config=config))
```

### HTTP Client (aiohttp)
**Always use async context managers**:
```python
async with aiohttp.ClientSession(base_url=url, headers=headers) as session:
    async with session.post(endpoint, data=data) as res:
        response = await res.json()
```

## Documentation Standards

**Docstrings**: Not currently used in the codebase
- Keep code self-explanatory through clear naming
- Add docstrings only for complex logic or public APIs

**Comments**: Use sparingly
- Only comment when code intent is not obvious
- Keep comments concise and relevant

**README**: Keep updated with user-facing changes

## File Structure

```
llmockapi/
├── src/llmockapi/       # Main package
│   ├── __init__.py      # App initialization & entry point
│   ├── client.py        # LLM client
│   ├── config.py        # Configuration
│   ├── middleware.py    # Request middleware
│   └── internal_route.py # Debug endpoints
├── tests/               # Test files (currently empty)
├── pyproject.toml       # Project metadata
└── .env                 # Environment variables (not in git)
```

## Key Architectural Patterns

1. **Middleware-Based Interception**: All non-internal requests go through `MockResponseMiddleWare`
2. **Conversation History**: Maintain LLM context in `request.state.messages`
3. **Settings-Based Config**: Use Pydantic Settings with env file support
4. **Internal Routes**: Debug endpoints under `/__internal/*` path
5. **Async Throughout**: All I/O operations use async/await

## Common Pitfalls to Avoid

1. **Don't use sync I/O**: Never use `requests`, always use `aiohttp`
2. **Don't skip async/await**: This will break the async event loop
3. **Don't add unnecessary dependencies**: Keep the project minimal
4. **Don't ignore EditorConfig**: Respect `.editorconfig` settings
5. **Don't commit secrets**: `.env` and `.envrc` are gitignored

## Version Control

**Git Ignore**: Respect `.gitignore` patterns
- Don't commit `__pycache__`, `*.pyc`, `*.pyo`
- Don't commit `.env`, `.envrc`
- Don't commit `.venv` or virtual environments
- Don't commit build artifacts (`dist/`, `*.egg-info`)

## Additional Notes

- This is a development tool, not production software
- Prioritize simplicity and readability over optimization
- Follow existing patterns in the codebase
- When in doubt, check existing code for reference
