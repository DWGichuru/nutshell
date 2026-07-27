import os

from anthropic import Anthropic

from backend.adapters.summarization.base import SummarizationError, SummaryFormat, SummaryInput, build_prompt

MODEL = "claude-opus-5"


def summarize(input: SummaryInput, format: SummaryFormat) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SummarizationError("ANTHROPIC_API_KEY is not set")

    client = Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": build_prompt(input, format)}],
        )
    except Exception as exc:
        raise SummarizationError(f"Anthropic summarization failed: {exc}") from exc

    return next((block.text for block in response.content if block.type == "text"), "")
