# llmockapi

An LLM-powered mock API server that dynamically generates realistic API responses based on OpenAPI/Swagger specifications.

## Overview

llmockapi is a Python-based development tool that uses Large Language Models to automatically generate mock API responses according to your API specifications. Instead of manually creating mock data, simply provide an OpenAPI/Swagger spec and let the LLM handle the response generation intelligently.

## Features

- **LLM-Powered Responses**: Uses AI models to generate contextually appropriate API responses
- **OpenAPI/Swagger Support**: Works with standard API specifications in JSON or YAML format
- **Flexible Spec Loading**: Load specifications from local files or HTTP URLs
- **Conversation History**: Maintains context across requests for consistent mock data
- **Debug UI**: Built-in web interface to view request/response history
- **FastAPI-Based**: Fast, modern Python web framework with async support
- **Configurable**: Control via environment variables or CLI arguments

## Requirements

- Python >= 3.12
- An LLM API endpoint (compatible with OpenAI chat completions format)
- API key for your LLM provider

## Installation

```bash
# Install using pip
pip install llmockapi

# Or install from source
git clone https://github.com/yourusername/llmockapi.git
cd llmockapi
pip install -e .
```

## Configuration

Configure llmockapi using environment variables, a `.env` file, or CLI arguments:

### Required Configuration

| Parameter | Environment Variable | CLI Argument | Description |
|-----------|---------------------|--------------|-------------|
| API Key | `API_KEY` | `--api-key` | Your LLM provider API key |
| Base URL | `BASE_URL` | `--base-url` | LLM API endpoint URL |
| API Spec | `MOCK_API_SPEC` | `--mock-api-spec` | Path or URL to OpenAPI/Swagger spec |

### Optional Configuration

| Parameter | Environment Variable | CLI Argument | Default | Description |
|-----------|---------------------|--------------|---------|-------------|
| Model | `MODEL` | `--model` | `anthropic/claude-haiku-4.5` | LLM model to use |
| Host | `HOST` | `--host` | `localhost` | Server host |
| Port | `PORT` | `--port` | `9000` | Server port |

### Example `.env` file:

```env
API_KEY=your-api-key-here
BASE_URL=https://api.yourlm-provider.com
MOCK_API_SPEC=./tests/mocks/api_specs.json
MODEL=anthropic/claude-haiku-4.5
HOST=localhost
PORT=9000
```

## Usage

### Starting the Server

```bash
# Using the CLI with environment variables
llmockapi

# Or with CLI arguments
llmockapi --api-key YOUR_KEY --base-url https://api.provider.com --mock-api-spec ./spec.json

# Or using Python module
python -m llmockapi
```

The server will start on `http://localhost:9000` (or your configured host/port).

### Making Requests

Once the server is running, make HTTP requests to any endpoint defined in your API specification:

```bash
# Example: Get a pet by ID
curl http://localhost:9000/pet/123

# Example: Create a new user
curl -X POST http://localhost:9000/user \
  -H "Content-Type: application/json" \
  -d '{"username": "johndoe", "email": "john@example.com"}'
```

## API Specifications

llmockapi supports OpenAPI/Swagger specifications in multiple formats:

### Local Files

```bash
# JSON format
llmockapi --mock-api-spec ./path/to/spec.json

# YAML format
llmockapi --mock-api-spec ./path/to/spec.yaml
```

### Remote URLs

```bash
# Load from HTTP/HTTPS
llmockapi --mock-api-spec https://example.com/api/swagger.json
```

## Internal Endpoints

llmockapi provides internal endpoints for debugging and monitoring:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/__internal/health` | GET | Health check endpoint |
| `/__internal/messages` | GET | View conversation history (JSON) |
| `/__internal/ui` | GET | Web UI to view request/response history |

### Example:

```bash
# Check server health
curl http://localhost:9000/__internal/health

# View conversation history
curl http://localhost:9000/__internal/messages

# Open web UI in browser
open http://localhost:9000/__internal/ui
```

## How It Works

1. **Initialization**: The server loads your API specification and creates a system prompt for the LLM
2. **Request Handling**: When a request arrives, llmockapi intercepts it via middleware
3. **LLM Processing**: The request details (method, path, headers, body) are sent to the LLM with the API spec as context
4. **Response Generation**: The LLM generates a contextually appropriate response matching your API specification
5. **History Tracking**: All requests and responses are stored in conversation history for consistency

The LLM maintains context across requests, ensuring that related API calls return consistent data (e.g., a created resource can be retrieved later).

## Example

Here's a quick example using the included Petstore API specification:

```bash
# Start the server with the example spec
llmockapi --api-key YOUR_KEY \
  --base-url https://api.provider.com \
  --mock-api-spec ./tests/mocks/api_specs.json

# Get pet by ID
curl http://localhost:9000/pet/1

# Create a new pet
curl -X POST http://localhost:9000/pet \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fluffy",
    "photoUrls": ["https://example.com/photo.jpg"],
    "status": "available"
  }'

# View the conversation in the web UI
open http://localhost:9000/__internal/ui
```

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/llmockapi.git
cd llmockapi

# Install dependencies
pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the server
llmockapi
```

## License

See the LICENSE file for details.

## Author

rbs392 (rbs392@yahoo.com)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
