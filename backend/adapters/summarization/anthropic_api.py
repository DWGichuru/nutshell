import os

from anthropic import Anthropic, AuthenticationError

from backend.adapters.summarization.base import SummarizationError, SummaryInput, build_prompt

MODEL = "claude-opus-5"


def summarize(input: SummaryInput) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SummarizationError("ANTHROPIC_API_KEY is not set")

    client = Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": build_prompt(input)}],
        )
    except AuthenticationError as exc:
        raise SummarizationError("Invalid Anthropic API key. Check your .env file.") from exc
    except Exception as exc:
        raise SummarizationError(f"Anthropic summarization failed: {exc}") from exc

    return next((block.text for block in response.content if block.type == "text"), "")
