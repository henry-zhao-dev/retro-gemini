"""Interactive chat sessions and Gemini conversation payloads."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Self

from prompt_toolkit import prompt

from retro_gemini import gemini_client, spinner

EXIT_COMMANDS = {"exit", "quit"}
SEPARATOR_WIDTH = 60


class MessageRole(StrEnum):
    USER = "user"
    MODEL = "model"


@dataclass(frozen=True, slots=True)
class ChatMessage:
    timestamp: str
    role: MessageRole
    content: str

    @classmethod
    def create(cls, role: MessageRole, content: str) -> Self:
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            role=role,
            content=content,
        )

    def to_api_payload(self) -> dict:
        return {"role": self.role.value, "parts": [{"text": self.content}]}


def _build_payload(messages: list[ChatMessage]) -> dict:
    return {"contents": [message.to_api_payload() for message in messages]}


def _print_header(model: str) -> None:
    print("=" * SEPARATOR_WIDTH)
    print("Retro Gemini CLI")
    print(f"   Model: {model}")
    print("-" * SEPARATOR_WIDTH)
    print("   * Press 'Enter' for a new line")
    print("   * Press 'Esc+Enter' to submit")
    print("   * Type 'exit' or 'quit' to leave")
    print("=" * SEPARATOR_WIDTH + "\n")


def _generate_response(
    user_prompt: str,
    model: str,
    conversation: list[ChatMessage],
    no_context: bool,
) -> str:
    user_message = ChatMessage.create(MessageRole.USER, user_prompt)
    conversation.append(user_message)

    if no_context:
        payload = _build_payload([user_message])
    else:
        payload = _build_payload(conversation)

    with spinner.loading_animation("Thinking"):
        response = gemini_client.generate(payload, model)

    conversation.append(ChatMessage.create(MessageRole.MODEL, response))

    return response


def _print_response(response: str) -> None:
    print("Gemini:")
    print(response)
    print("\n" + "-" * SEPARATOR_WIDTH + "\n")


def _print_api_error(error: gemini_client.GeminiAPIError) -> None:
    if error.status_code == 503:
        print(
            "Gemini servers are currently overloaded. "
            "Please wait a minute and try again, or "
            "select a different model (see --help)."
        )
    else:
        print(f"A Gemini API error occurred: {error}")


def start_chat(model: str, no_context: bool = False) -> None:
    _print_header(model)

    conversation: list[ChatMessage] = []

    while True:
        try:
            print("You:")
            user_prompt = prompt("> ", multiline=True).strip()

            if not user_prompt:
                continue

            if user_prompt.lower() in EXIT_COMMANDS:
                print("\nGoodbye!\n")
                return

            print()
            response = _generate_response(user_prompt, model, conversation, no_context)
            _print_response(response)

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            return

        except gemini_client.GeminiAPIError as error:
            _print_api_error(error)
            return

        except Exception as error:
            print(f"An unexpected error occurred: {error}")
            return
