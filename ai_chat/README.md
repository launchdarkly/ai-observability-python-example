# 🤖 LangChain Tools with LaunchDarkly Integration

A powerful CLI tool that combines LangChain's capabilities with LaunchDarkly's AI configuration management. Built with Python and Poetry for easy dependency management.

## ✨ Features

### Core Features
- 🔍 **Search Tool**: Get information about current events using DuckDuckGo
- 🧮 **Calculator Tool**: Solve mathematical problems using LangChain's math chain
- 💬 Interactive CLI interface with rich formatting
- 🔄 Continuous conversation flow
- 🔥 Hot reload during development

### LaunchDarkly Integration
- 🎯 **Dynamic Model Configuration**: Change AI models through LaunchDarkly
- 📊 **AI Metrics Tracking**: Automatic tracking of AI model usage
- 🧪 **A/B Testing**: Test different AI configurations with different user segments
- 🛡️ **Fallback Support**: Graceful degradation when LaunchDarkly is unavailable

### Development Features
- 🛠️ Built with Poetry for easy dependency management
- 🔌 Optional LaunchDarkly integration (can be disabled)
- 🎪 Clean separation of concerns with modular architecture

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Poetry (install from [python-poetry.org](https://python-poetry.org/docs/#installation))
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- LaunchDarkly SDK key (optional - [get one here](https://app.launchdarkly.com/settings/projects))

### Installation

1. **Clone or download this project**

2. **Install dependencies using Poetry:**
   ```bash
   poetry install
   ```

3. **Set up your API keys:**
   
   Create a `.env` file in the project directory:
   ```bash
   # Required: OpenAI API key
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   
   # Optional: LaunchDarkly SDK key (for AI config management)
   echo "LAUNCHDARKLY_SDK_KEY=your_launchdarkly_sdk_key_here" >> .env
   ```
   
   Or export them as environment variables:
   ```bash
   export OPENAI_API_KEY=your_openai_api_key_here
   export LAUNCHDARKLY_SDK_KEY=your_launchdarkly_sdk_key_here  # optional
   ```

4. **Run the application:**
   ```bash
   poetry run langchain-tools
   ```

## 🎮 Usage

### Available Tools

1. **Search Tool**
   - Get real-time information about current events
   - Uses DuckDuckGo for web searches
   - Example: "What's the latest news about AI technology?"

2. **Calculator Tool**
   - Solve mathematical problems
   - Uses LangChain's math chain
   - Example: "What is the square root of 144 plus 50?"

### Command Line Options

```bash
# Basic usage with LaunchDarkly (default)
poetry run langchain-tools

# Use a different model as fallback
poetry run langchain-tools --model gpt-4

# Disable LaunchDarkly and use direct OpenAI integration
poetry run langchain-tools --disable-launchdarkly

# Specify API keys directly
poetry run langchain-tools --api-key your_openai_key --launchdarkly-sdk-key your_ld_key

# Development mode with hot reload
poetry run dev
```

### Available Commands

- **Chat**: Just type your question and press Enter
- **Exit**: Type `exit`, `quit`, or `bye` to end the session
- **Help**: Type `help` to see available commands

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required: OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Optional: LaunchDarkly Configuration  
LAUNCHDARKLY_SDK_KEY=your_launchdarkly_sdk_key_here

# Optional: Default Configuration
AI_CONFIG_KEY=langchain-tools-config
DEFAULT_MODEL=gpt-3.5-turbo
```

### LaunchDarkly AI Config Setup

To use LaunchDarkly AI Configs for dynamic model and configuration management:

1. Create an AI Config in your LaunchDarkly dashboard with key `langchain-tools-config`
2. Configure model settings and targeting rules
3. Changes will be applied in real-time without requiring application restart

## 🏗️ Project Structure

```
langchain/
├── langchain_tools/           # Main package
│   ├── __init__.py           # Package initialization
│   ├── agent.py              # LangChain agent with tools
│   ├── cli.py                # CLI interface
│   └── dev.py                # Development server with hot reload
├── pyproject.toml            # Poetry configuration
├── README.md                 # This file
└── .env                      # Environment variables (create this)
```

## 🔧 Development

### Setting up for Development

```bash
# Install development dependencies
poetry install

# Format code
poetry run black langchain_tools/

# Run with hot reload
poetry run dev
```

## 🔐 Security Notes

- Never commit your `.env` file to version control
- Keep your API keys secure and don't share them
- The application does not persist any conversation data
- LaunchDarkly connections are properly closed on exit

## 📄 License

This project is provided as-is for educational and personal use.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve this project!