"""Command-line parsing and application startup."""

import argparse
import os
import sys

from dotenv import load_dotenv

from retro_gemini import chat, gemini_client
from retro_gemini.settings import AppSettings


def parse_args(default_model: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Retro Gemini CLI - Interactive terminal client for Google Gemini."
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List all available Gemini model names",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=default_model,
        help=f"Specify Gemini model to use (default: {default_model})",
    )
    parser.add_argument(
        "-dm",
        "--default-model",
        type=str,
        help="Permanently set the default model on start-up",
    )
    parser.add_argument(
        "-n",
        "--no-context",
        dest="no_context",
        action="store_true",
        help="Process each prompt without sending previous conversation context",
    )
    return parser.parse_args()


def require_api_key() -> None:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        print(
            "Error: GEMINI_API_KEY environment variable is not set.\n"
            "Please export it using: export GEMINI_API_KEY='your_key_here'",
            file=sys.stderr,
        )
        sys.exit(1)


def get_model_names() -> list[str]:
    try:
        return gemini_client.list_model_names()
    except gemini_client.GeminiAPIError as error:
        print(f"Failed to retrieve Gemini models: {error}", file=sys.stderr)
        sys.exit(1)


def handle_command(
    args: argparse.Namespace, settings: AppSettings, model_names: list[str]
) -> None:
    if args.list:
        print("\n".join(model_names))
    elif args.default_model:
        if args.default_model in model_names:
            settings.default_model = args.default_model
        else:
            print(
                f"Model not found: {args.default_model}.\n"
                "Please run retro-gemini --list to view all available Gemini models."
            )
            sys.exit(1)
    elif args.model in model_names:
        chat.start_chat(args.model, args.no_context)
    else:
        print(
            f"Model not found: {args.model}.\n"
            "Please run retro-gemini --list to view all available Gemini models."
        )
        sys.exit(1)


def main() -> None:
    settings = AppSettings.load()
    args = parse_args(settings.default_model)
    require_api_key()

    handle_command(args, settings, get_model_names())
    settings.save()
    print(f"Settings saved to: {settings.get_path()}")


if __name__ == "__main__":
    main()
