import argparse
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.spinner import Spinner
from rich.table import Table
from rich import box

from providers import (
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    BaseProvider,
)


console = Console()


def mask_api_key(api_key: str) -> str:
    """Mask API key for display, showing only first 4 and last 4 characters."""
    if len(api_key) <= 12:
        return "*" * len(api_key)
    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"


def display_provider_info(provider: BaseProvider) -> None:
    """Display provider configuration information."""
    info_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    info_table.add_column("Key", style="bold cyan")
    info_table.add_column("Value", style="white")

    info_table.add_row("Provider", Text(provider.name, style="bold magenta"))
    info_table.add_row("API Key", Text(mask_api_key(provider.api_key), style="yellow"))
    info_table.add_row("Base URL", Text(provider.base_url or "(default)", style="green"))

    console.print(Panel(
        info_table,
        title="[bold]Provider Configuration[/bold]",
        border_style="blue",
        padding=(0, 1),
    ))
    console.print()


def get_provider(
    provider_name: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    system_prompt: Optional[str] = None,
    default_model: Optional[str] = None,
) -> BaseProvider:
    """Get provider instance by name."""
    providers = {
        "openai": (
            OpenAIProvider,
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "OPENAI_SYSTEM_PROMPT",
            "OPENAI_DEFAULT_MODEL",
        ),
        "anthropic": (
            AnthropicProvider,
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_BASE_URL",
            "ANTHROPIC_SYSTEM_PROMPT",
            "ANTHROPIC_DEFAULT_MODEL",
        ),
        "gemini": (
            GeminiProvider,
            "GEMINI_API_KEY",
            None,  # Gemini doesn't support custom base_url in SDK
            "GEMINI_SYSTEM_PROMPT",
            "GEMINI_DEFAULT_MODEL",
        ),
    }

    if provider_name not in providers:
        raise ValueError(f"Unknown provider: {provider_name}")

    provider_class, key_env, url_env, system_env, model_env = providers[provider_name]

    # Use provided values or fall back to environment variables
    final_api_key = api_key or os.getenv(key_env)
    final_base_url = base_url or (os.getenv(url_env) if url_env else None)
    final_system_prompt = system_prompt or os.getenv(system_env)
    final_default_model = default_model or os.getenv(model_env)

    if not final_api_key:
        raise ValueError(f"API key not provided for {provider_name}. Set {key_env} in .env or use --api-key")

    return provider_class(
        api_key=final_api_key,
        base_url=final_base_url,
        system_prompt=final_system_prompt,
        default_model=final_default_model,
    )


def display_models(provider: BaseProvider) -> None:
    """Display models in a rich table."""
    try:
        display_provider_info(provider)

        models = provider.list_models()

        table = Table(
            title=f"[bold blue]{provider.name} Models[/bold blue]",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Model ID", style="green")
        table.add_column("Name", style="yellow")
        table.add_column("Description", style="white", max_width=50)

        for model in models:
            table.add_row(
                model.id,
                model.name or "-",
                (model.description[:47] + "...") if model.description and len(model.description) > 50 else (model.description or "-"),
            )

        console.print(table)
        console.print(f"\n[bold green]Total: {len(models)} models[/bold green]")

    except Exception as e:
        console.print(Panel(
            f"[bold red]Error fetching models from {provider.name}:[/bold red]\n{str(e)}",
            title="Error",
            border_style="red",
        ))
        sys.exit(1)


def validate_key(provider: BaseProvider) -> None:
    """Validate API key and display result."""
    display_provider_info(provider)

    console.print(f"[bold]Validating {provider.name} API key...[/bold]")

    if provider.validate_key():
        console.print(Panel(
            f"[bold green]API key is valid![/bold green]",
            title=f"{provider.name} Key Validation",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[bold red]API key is invalid![/bold red]",
            title=f"{provider.name} Key Validation",
            border_style="red",
        ))
        sys.exit(1)


def create_response_panel(provider_name: str, content: str, done: bool = False) -> Panel:
    """Create a panel for streaming response."""
    title = f"[bold]{provider_name}[/bold]"
    border_style = "green" if done else "blue"
    title_suffix = " (done)" if done else f" [cyan]Generating...[/cyan]"

    return Panel(
        Text(content, style="white"),
        title=title + title_suffix,
        border_style=border_style,
        expand=True,
        padding=(1, 2),
    )


def chat_single_provider(
    provider: BaseProvider,
    message: str,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> tuple[str, str, bool]:
    """
    Chat with a single provider and return result.

    Returns:
        tuple of (provider_name, content, success)
    """
    try:
        content = ""
        for chunk in provider.chat(message, model=model, system_prompt=system_prompt, stream=True):
            content += chunk
        return (provider.name, content, True)
    except Exception as e:
        return (provider.name, f"Error: {str(e)}", False)


def chat_all_providers(message: str, provider_name: Optional[str] = None, model: Optional[str] = None, system_prompt: Optional[str] = None) -> None:
    """Chat with all providers simultaneously and display results with Rich."""

    provider_names = [provider_name] if provider_name else ["openai", "anthropic", "gemini"]

    providers = []
    for name in provider_names:
        try:
            provider = get_provider(name, system_prompt=system_prompt, default_model=model)
            providers.append(provider)
        except ValueError as e:
            console.print(Panel(
                f"[yellow]{str(e)}[/yellow]",
                title="Warning",
                border_style="yellow",
            ))

    if not providers:
        console.print(Panel(
            "[bold red]No providers available. Check your .env configuration.[/bold red]",
            title="Error",
            border_style="red",
        ))
        sys.exit(1)

    # Initialize empty content for each provider
    provider_contents = {p.name: "" for p in providers}
    provider_done = {p.name: False for p in providers}
    provider_model = {p.name: model or p.default_model or "(default)" for p in providers}

    def update_display():
        """Generate the current display layout."""
        panels = []
        for provider in providers:
            status = "[bold green](done)[/bold green]" if provider_done[provider.name] else "[cyan]Generating...[/cyan]"
            border = "green" if provider_done[provider.name] else "blue"
            title = f"[bold]{provider.name}[/bold] [cyan][[/cyan][yellow]{provider_model[provider.name]}[/yellow][cyan]][/cyan] {status}"
            panels.append(Panel(
                Text(provider_contents[provider.name], style="white"),
                title=title,
                border_style=border,
                expand=True,
                padding=(1, 2),
            ))
        return Group(*panels)

    def run_provider(provider: BaseProvider) -> None:
        """Run chat for a single provider in a thread."""
        try:
            content = ""
            for chunk in provider.chat(message, model=model, system_prompt=system_prompt, stream=True):
                provider_contents[provider.name] += chunk
            provider_done[provider.name] = True
        except Exception as e:
            provider_contents[provider.name] = f"Error: {str(e)}"
            provider_done[provider.name] = True

    # Start all providers in parallel threads
    threads = []
    for provider in providers:
        t = threading.Thread(target=run_provider, args=(provider,))
        t.start()
        threads.append(t)

    # Display with Live for streaming updates
    with Live(update_display(), console=console, refresh_per_second=10) as live:
        for t in threads:
            t.join()

    # Final display with all done
    console.clear()
    final_panels = []
    for provider in providers:
        title = f"[bold]{provider.name}[/bold] [cyan][[/cyan][yellow]{provider_model[provider.name]}[/yellow][cyan]][/cyan] [bold green](done)[/bold green]"
        final_panels.append(Panel(
            Text(provider_contents[provider.name], style="white"),
            title=title,
            border_style="green",
            expand=True,
            padding=(1, 2),
        ))
    console.print(Group(*final_panels))


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Check API keys for OpenAI, Anthropic, and Gemini, or chat with all providers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run main.py openai                    # List OpenAI models using .env
  uv run main.py anthropic --validate      # Validate Anthropic API key
  uv run main.py gemini --api-key YOUR_KEY # Use custom API key
  uv run main.py openai --base-url https://custom.api.com/v1
  uv run main.py chat "Hello, how are you?"  # Chat with all providers
  uv run main.py chat "Tell me a joke" --model gpt-4o  # Use specific model
  uv run main.py chat "Hello" --system-prompt "You are a pirate"  # Custom system prompt
  uv run main.py chat "Hello" -p openai    # Chat with only OpenAI
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Model listing command (default behavior)
    list_parser = subparsers.add_parser("list", help="List models for a provider")
    list_parser.add_argument(
        "provider",
        choices=["openai", "anthropic", "gemini"],
        help="API provider to check",
    )
    list_parser.add_argument(
        "--api-key",
        "-k",
        help="API key (overrides .env)",
    )
    list_parser.add_argument(
        "--base-url",
        "-b",
        help="Base URL for the API (overrides .env)",
    )
    list_parser.add_argument(
        "--validate",
        "-v",
        action="store_true",
        help="Only validate the API key without listing models",
    )

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Chat with all providers simultaneously")
    chat_parser.add_argument(
        "message",
        help="Message to send to all providers",
    )
    chat_parser.add_argument(
        "--provider",
        "-p",
        choices=["openai", "anthropic", "gemini"],
        help="Specific provider to chat with (default: all providers)",
    )
    chat_parser.add_argument(
        "--model",
        "-m",
        help="Model to use (overrides .env default model)",
    )
    chat_parser.add_argument(
        "--system-prompt",
        "-s",
        help="System prompt (overrides .env system prompt)",
    )

    args = parser.parse_args()

    if args.command == "chat":
        # Chat mode - talk to all providers simultaneously
        chat_all_providers(
            message=args.message,
            provider_name=args.provider,
            model=args.model,
            system_prompt=args.system_prompt,
        )
    else:
        # List mode (default)
        provider_name = args.provider if args.command == "list" else args.provider

        try:
            provider = get_provider(
                provider_name,
                api_key=args.api_key,
                base_url=args.base_url,
            )

            if args.validate:
                validate_key(provider)
            else:
                display_models(provider)

        except ValueError as e:
            console.print(Panel(
                f"[bold red]{str(e)}[/bold red]",
                title="Configuration Error",
                border_style="red",
            ))
            sys.exit(1)


if __name__ == "__main__":
    main()
