# Support Orchestrator

AI-powered customer support assistant using OpenAI function calling with LaunchDarkly feature flags and OpenTelemetry observability.

## Features

- **OpenAI Function Calling** - Smart routing to support tools
- **LaunchDarkly Flags** - Control behavior with feature flags
- **Full Observability** - OpenTelemetry tracing throughout

## Tools

- Create support tickets
- Fetch order status  
- Reset passwords

## Quick Start

**Create and activate virtual environment:**
```bash
python3 -m venv .venv && source .venv/bin/activate
```

**Install dependencies:**
```bash
pip install openai opentelemetry-sdk opentelemetry-exporter-otlp \
            opentelemetry-instrumentation-openai python-dotenv \
            launchdarkly-server-sdk launchdarkly-observability
```

**Set environment variables:**
```bash
export OPENAI_API_KEY="sk-..."
export LAUNCHDARKLY_SDK_KEY="sdk-..."  # optional
```

**Run:**
```bash
# Interactive mode
python support_orchestrator.py

# Single message
python support_orchestrator.py --message "Where is order #A1234?"
```

## Feature Flags

- `priority-routing` - Auto-escalate urgent tickets
- `max-response-length` - Limit response size
- `enhanced-responses` - Detailed responses

## Test Orders

Try these order IDs: `A1234` (shipped), `B5678` (processing), `C9012` (delivered)

