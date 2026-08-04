import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime

from dotenv import load_dotenv
from prompt_toolkit import prompt

from retro_gemini import gemini_client


@dataclass(frozen=True)
class MessageLog:
    timestamp: str
    role: str
    content: str

    @classmethod
    def create(cls, role: str, content: str):
        """Factory method to easily create a new log with current timestamp."""
        return cls(
            # Example: 2023-10-24T14:32:05.123456
            timestamp=datetime.now().isoformat(),
            role=role,
            content=content,
        )

    def to_api_payload(self) -> dict:
        """Strips the timestamp for the LLM API."""
        return {"role": self.role, "parts": [{"text": self.content}]}


def start_chat(model: str, no_history: bool = False):
    # Header Layout
    print("=" * 60)
    print("Retro Gemini CLI")
    print(f"   Model: {model}")
    print("-" * 60)
    print("   * Press 'Enter' for a new line")
    print("   * Press 'Esc+Enter' to submit")
    print("   * Type 'exit' or 'quit' to leave")
    print("=" * 60 + "\n")

    history: list[MessageLog] = []

    while True:
        try:
            print("You:")
            user_prompt = prompt("> ", multiline=True).strip()

            if not user_prompt:
                continue

            if user_prompt.lower() in ("exit", "quit"):
                print("\nGoodbye!\n")
                break

            if not no_history:
                log = MessageLog.create("user", user_prompt)
                history.append(log)
                payload = {"contents": [log.to_api_payload() for log in history]}
            else:
                payload = gemini_client.single_payload(user_prompt)

            response = gemini_client.generate(payload, model)

            print("\nGemini:")
            print(response)
            print("\n" + "-" * 60 + "\n")

            if not no_history:
                log = MessageLog.create("model", response)
                history.append(log)

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        except gemini_client.GeminiAPIError as e:
            if "503" in str(e):
                print(
                    "Gemini servers are currently overloaded. "
                    "Please wait a minute and try again."
                )
            else:
                print(f"A Gemini API error occurred: {e}")
            break

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
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
    parser.add_argument(
        "-n",
        "--no-history",
        action="store_true",
        help="Process prompt without sending previous conversation history",
    )

    args = parser.parse_args()

    load_dotenv()

    # Validate environment variable
    if not os.getenv("GEMINI_API_KEY"):
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
        start_chat(args.model, args.no_history)
    else:
        print(
            f"Model not found: {args.model}.\n"
            "Please run retro-gemini --list to view all available Gemini models."
        )


if __name__ == "__main__":
    main()
