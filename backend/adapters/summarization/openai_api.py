import os

from openai import OpenAI

from backend.adapters.summarization.base import SummarizationError, SummaryInput, build_prompt

MODEL = "gpt-4o-mini"


def summarize(input: SummaryInput) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SummarizationError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": build_prompt(input)}],
        )
    except Exception as exc:
        raise SummarizationError(f"OpenAI summarization failed: {exc}") from exc

    return response.choices[0].message.content or ""
