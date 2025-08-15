# AI Chat

A CLI chat interface using OpenAI with LaunchDarkly AI Config and Observability integration.

## Features

- Interactive CLI chat with OpenAI's GPT models
- LaunchDarkly AI Config integration for dynamic prompts and models
- LaunchDarkly Observability for tracing and metrics
- OpenLLMetry integration for OpenAI instrumentation
- Hot reload during development

## Installation

```bash
# Install dependencies
poetry install

# Create .env file
cp .env.example .env
```

## Environment Setup

```env
OPENAI_API_KEY=your_openai_api_key
LAUNCHDARKLY_SDK_KEY=your_launchdarkly_sdk_key  # Optional
```

## Usage

### Development (with hot reload)
```bash
poetry run chat-dev
```

### Production
```bash
poetry run ai-chat
```

### CLI Options
```bash
poetry run ai-chat --help
```

- `--api-key`: OpenAI API key (can also use env var)
- `--model`: OpenAI model (default: gpt-3.5-turbo)
- `--launchdarkly-sdk-key`: LaunchDarkly SDK key (can also use env var)

## Commands

- Type your message and press Enter to chat
- `clear` - Clear conversation history
- `help` - Show help message
- `exit`, `quit`, or `bye` - End session