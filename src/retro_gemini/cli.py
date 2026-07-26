import argparse
import os
import sys

from prompt_toolkit import prompt

from retro_gemini import gemini_client


def start_chat(model: str):
    # Header Layout
    print("=" * 60)
    print("Retro Gemini CLI")
    print(f"   Model: {model}")
    print("-" * 60)
    print("   * Press 'Enter' for a new line")
    print("   * Press 'Esc+Enter' to submit")
    print("   * Type 'exit' or 'quit' to leave")
    print("=" * 60 + "\n")

    while True:
        try:
            print("You:")
            user_input = prompt("> ", multiline=True).strip()

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                print("\nGoodbye!\n")
                break

            response = gemini_client.generate(user_input, model)

            print("\nGemini:")
            print(response)
            print("\n" + "-" * 60 + "\n")

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break


def main():
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
        default="gemini-flash-latest",
        help="Specify Gemini model to use (default: gemini-flash-latest)",
    )

    args = parser.parse_args()

    # Validate environment variable
    if not os.environ.get("GEMINI_API_KEY"):
        print(
            "Error: GEMINI_API_KEY environment variable is not set.\n"
            "Please export it using: export GEMINI_API_KEY='your_key_here'",
            file=sys.stderr,
        )
        sys.exit(1)

    model_names = gemini_client.list_model_names()
    if args.list:
        print("\n".join(model_names))
    elif args.model in model_names:
        start_chat(args.model)
    else:
        print(
            f"Model not found: {args.model}.\n"
            "Please run retro-gemini --list to view all available Gemini models."
        )


if __name__ == "__main__":
    main()
