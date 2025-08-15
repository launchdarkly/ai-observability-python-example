import click
import sys
from typing import Optional
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt

from .agent import LangChainAgent

load_dotenv()
console = Console()

def format_response(response: str) -> None:
    console.print(Panel(Markdown(response), border_style="cyan"))

def format_error(error_message: str) -> None:
    console.print(Panel(f"Error: {error_message}", border_style="red"))

@click.command()
@click.option("--api-key", help="OpenAI API key")
@click.option("--ld-sdk-key", help="LaunchDarkly SDK key")
@click.option(
    "--ai-config-key",
    default="lang-chain-agent-config",
    help="LaunchDarkly AI config key"
)
@click.option(
    "--context-key",
    default="default-langchain-user",
    help="LaunchDarkly context key"
)
def main(
    api_key: Optional[str],
    ld_sdk_key: Optional[str],
    ai_config_key: str,
    context_key: str
):
    """LangChain Agent CLI with OpenAI and LaunchDarkly integration."""
    console.print(Panel(
        Markdown("""
# LangChain Tools CLI

Available Tools:
- Search: Get information about current events
- Calculator: Solve mathematical problems

Commands:
- Type your question and press Enter
- exit/quit/bye: End session
- help: Show this message
"""),
        border_style="blue"
    ))

    try:
        agent = LangChainAgent(
            openai_api_key=api_key,
            launchdarkly_sdk_key=ld_sdk_key,
            ai_config_agent_key=ai_config_key,
            context_key=context_key
        )

        while True:
            try:
                user_input = Prompt.ask("\nYou").strip()
                if user_input.lower() in ["exit", "quit", "bye"]:
                    break
                elif user_input.lower() == "help":
                    continue
                elif not user_input:
                    continue

                response = agent.run_agent(user_input)
                format_response(response)

            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                format_error(str(e))

    except ValueError as e:
        format_error(f"Setup error: {e}")
        console.print("Set OPENAI_API_KEY in .env file or use --api-key")
    except Exception as e:
        format_error(str(e))
    finally:
        if 'agent' in locals():
            agent.close()

if __name__ == "__main__":
    main()