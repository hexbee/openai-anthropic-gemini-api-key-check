import argparse
import os
import sys
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.text import Text

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
) -> BaseProvider:
    """Get provider instance by name."""
    providers = {
        "openai": (
            OpenAIProvider,
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
        ),
        "anthropic": (
            AnthropicProvider,
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_BASE_URL",
        ),
        "gemini": (
            GeminiProvider,
            "GEMINI_API_KEY",
            None,  # Gemini doesn't support custom base_url in SDK
        ),
    }

    if provider_name not in providers:
        raise ValueError(f"Unknown provider: {provider_name}")

    provider_class, key_env, url_env = providers[provider_name]

    # Use provided values or fall back to environment variables
    final_api_key = api_key or os.getenv(key_env)
    final_base_url = base_url or (os.getenv(url_env) if url_env else None)

    if not final_api_key:
        raise ValueError(f"API key not provided for {provider_name}. Set {key_env} in .env or use --api-key")

    return provider_class(api_key=final_api_key, base_url=final_base_url)


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


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Check API keys for OpenAI, Anthropic, and Gemini by listing models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run main.py openai                    # List OpenAI models using .env
  uv run main.py anthropic --validate      # Validate Anthropic API key
  uv run main.py gemini --api-key YOUR_KEY # Use custom API key
  uv run main.py openai --base-url https://custom.api.com/v1
        """,
    )

    parser.add_argument(
        "provider",
        choices=["openai", "anthropic", "gemini"],
        help="API provider to check",
    )
    parser.add_argument(
        "--api-key",
        "-k",
        help="API key (overrides .env)",
    )
    parser.add_argument(
        "--base-url",
        "-b",
        help="Base URL for the API (overrides .env)",
    )
    parser.add_argument(
        "--validate",
        "-v",
        action="store_true",
        help="Only validate the API key without listing models",
    )

    args = parser.parse_args()

    try:
        provider = get_provider(
            args.provider,
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
