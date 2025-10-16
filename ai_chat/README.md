# AI Chat CLI

A CLI chat interface using OpenAI with LaunchDarkly AI Config and OpenTelemetry integration.

## Setup

### Prerequisites
- Python 3.10 or higher
- Poetry for dependency management
- OpenAI API key
- LaunchDarkly SDK key (optional)

### Installation
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
poetry install

# Create .env file
cp .env.example .env
```

### Environment Variables
```env
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional
LAUNCHDARKLY_SDK_KEY=your_launchdarkly_sdk_key
OTEL_SERVICE_NAME=ai-chat-cli
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318/v1/traces
OTEL_DEBUG=true  # For development
```

## Usage

### Development Mode (with hot reload)
```bash
poetry run watch
```

### Regular Mode
```bash
poetry run dev
```

### CLI Options
```bash
poetry run dev --help
```

Available options:
- `--api-key`: OpenAI API key (can also use env var)
- `--model`: OpenAI model (default: gpt-3.5-turbo)
- `--launchdarkly-sdk-key`: LaunchDarkly SDK key (can also use env var)

### Chat Commands
- Type your message and press Enter to chat
- `clear`: Clear conversation history
- `help`: Show help message
- `exit`, `quit`, or `bye`: End session

## LaunchDarkly Integration

The project uses LaunchDarkly for:
1. Dynamic AI configuration (prompts, models)
2. Observability and metrics
3. A/B testing capabilities

To enable LaunchDarkly features:
1. Set `LAUNCHDARKLY_SDK_KEY` in your .env file
2. Create a flag in your LaunchDarkly project with key: `ai-observability-python-chat`

## OpenTelemetry Integration

OpenTelemetry instrumentation is included for:
- OpenAI API calls tracing
- Request/response monitoring
- Performance metrics

To view traces:
1. Set up an OpenTelemetry collector
2. Configure `OTEL_EXPORTER_OTLP_ENDPOINT`
3. Enable debug mode with `OTEL_DEBUG=true` for console output

## Development

The project supports hot reload during development:
```bash
poetry run watch
```

This will automatically restart the application when code changes are detected.