"""CLI interface for the AI chat application."""

import sys
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from dotenv import load_dotenv

from .openai_client import OpenAIClient

load_dotenv()
console = Console()

def format_response(response: str, is_error: bool = False) -> None:
    console.print(Panel(
        Markdown(response) if not is_error else response,
        border_style="red" if is_error else "cyan"
    ))

@click.command()
@click.option("--api-key", help="OpenAI API key")
@click.option("--model", default="gpt-3.5-turbo", help="OpenAI model to use")
@click.option("--launchdarkly-sdk-key", help="LaunchDarkly SDK key")
def main(api_key: Optional[str], model: str, launchdarkly_sdk_key: Optional[str]):
    """AI Chat CLI - Have a conversation with OpenAI's GPT model."""
    console.print(Panel(
        Markdown("""
# AI Chat CLI

Commands:
- Type your message and press Enter
- exit/quit/bye: End session
- clear: Clear history
- help: Show this message
"""),
        border_style="blue"
    ))
    
    try:
        client = OpenAIClient(
            api_key=api_key,
            model=model,
            launchdarkly_sdk_key=launchdarkly_sdk_key
        )
        
        while True:
            try:
                user_input = Prompt.ask("\nYou").strip()
                
                if user_input.lower() in ["exit", "quit", "bye"]:
                    break
                elif user_input.lower() == "clear":
                    client.clear_history()
                    continue
                elif user_input.lower() == "help" or not user_input:
                    continue
                
                response = client.get_response(user_input)
                format_response(response)
                
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                format_response(str(e), is_error=True)
                
    except ValueError as e:
        format_response(
            "OpenAI API key is required. Set OPENAI_API_KEY in .env file or use --api-key",
            is_error=True
        )
    except Exception as e:
        format_response(str(e), is_error=True)
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    main()