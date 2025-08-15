# AI Observability Python

This repository contains two Python projects demonstrating AI observability with LaunchDarkly:

1. **AI Chat**: A simple CLI chat interface using OpenAI
2. **LangChain Tools**: A CLI tool with multiple AI capabilities using LangChain

## Common Requirements

- Python 3.10 or higher
- Poetry for dependency management
- OpenAI API key
- LaunchDarkly SDK key (optional)

## AI Chat Project

A straightforward CLI chat interface with OpenAI's GPT models.

### Setup
```bash
# Navigate to the project
cd ai_chat

# Install dependencies
poetry install

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Usage
```bash
# Development mode with hot reload
poetry run watch

# Regular mode
poetry run dev

# CLI options
poetry run dev --help
```

Available commands in chat:
- Type your message and press Enter
- `clear`: Clear conversation history
- `help`: Show help message
- `exit`, `quit`, or `bye`: End session

## LangChain Tools Project

A more advanced CLI tool with multiple AI capabilities using LangChain.

### Setup
```bash
# Navigate to the project
cd langchain_tools

# Install dependencies
poetry install

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables
```env
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional
LAUNCHDARKLY_SDK_KEY=your_launchdarkly_sdk_key
OTEL_SERVICE_NAME=langchain-tools
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces
OTEL_DEBUG=true  # For development
```

### Usage
```bash
# Development mode with hot reload
poetry run watch

# Regular mode
poetry run dev

# CLI options
poetry run dev --help
```

Available commands:
- Type your question and press Enter
- `help`: Show help message
- `exit`, `quit`, or `bye`: End session

## LaunchDarkly Integration

Both projects support LaunchDarkly for:
1. Dynamic AI configuration
2. Observability and metrics
3. A/B testing of prompts and models

To enable LaunchDarkly features:
1. Set `LAUNCHDARKLY_SDK_KEY` in your .env file
2. Create corresponding flags in your LaunchDarkly project:
   - For AI Chat: `ai-observability-python-chat`
   - For LangChain Tools: `langchain-agent-config`

## OpenTelemetry Integration

Both projects include OpenTelemetry instrumentation:
- AI Chat: Traces OpenAI API calls
- LangChain Tools: Traces both OpenAI and LangChain operations

To view traces:
1. Set up an OpenTelemetry collector
2. Configure `OTEL_EXPORTER_OTLP_ENDPOINT`
3. Enable debug mode with `OTEL_DEBUG=true` for console output

## Development

Both projects support hot reload during development:
```bash
poetry run watch  # In either project directory
```

This will automatically restart the application when code changes are detected.