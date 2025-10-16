# LangChain Tools

A LangChain-based CLI tool with multiple tools and LaunchDarkly integration.

## Setup

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
```

## Usage

```bash
# Run the agent
poetry run dev
```