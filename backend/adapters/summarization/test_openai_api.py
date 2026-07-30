import pytest

from backend.adapters.summarization import openai_api
from backend.adapters.summarization.base import SummarizationError, SummaryInput
from backend.adapters.summarization.fakes import (
    FakeChatChoice,
    FakeChatCompletion,
    FakeChatMessage,
    FakeOpenAIClient,
)
from backend.adapters.transcription.base import TranscriptSegment


@pytest.fixture
def sample_input():
    return SummaryInput(
        text="hello world, this is a test transcript.",
        segments=[
            TranscriptSegment(start=0.0, end=5.0, text="hello world"),
            TranscriptSegment(start=65.0, end=70.0, text="this is a test transcript"),
        ],
    )


def test_summarize_returns_response_text(monkeypatch, sample_input):
    response = FakeChatCompletion(choices=[FakeChatChoice(message=FakeChatMessage(content="# summary"))])
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(openai_api, "OpenAI", lambda api_key: FakeOpenAIClient(response=response))

    result = openai_api.summarize(sample_input)

    assert result == "# summary"


def test_summarize_includes_timestamps_when_segments_present(monkeypatch, sample_input):
    captured = {}

    class CapturingCompletions:
        def create(self, **kwargs):
            captured["prompt"] = kwargs["messages"][0]["content"]
            response = FakeChatCompletion(choices=[FakeChatChoice(message=FakeChatMessage(content="ok"))])
            return response

    class CapturingChat:
        completions = CapturingCompletions()

    class CapturingClient:
        chat = CapturingChat()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(openai_api, "OpenAI", lambda api_key: CapturingClient())

    openai_api.summarize(sample_input)

    assert "1:05" in captured["prompt"]


def test_summarize_falls_back_to_plain_text_without_segments(monkeypatch):
    input_without_segments = SummaryInput(text="hello world, this is a test transcript.", segments=[])
    captured = {}

    class CapturingCompletions:
        def create(self, **kwargs):
            captured["prompt"] = kwargs["messages"][0]["content"]
            response = FakeChatCompletion(choices=[FakeChatChoice(message=FakeChatMessage(content="ok"))])
            return response

    class CapturingChat:
        completions = CapturingCompletions()

    class CapturingClient:
        chat = CapturingChat()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(openai_api, "OpenAI", lambda api_key: CapturingClient())

    openai_api.summarize(input_without_segments)

    assert "hello world, this is a test transcript." in captured["prompt"]


def test_summarize_missing_api_key_raises_before_client(monkeypatch, sample_input):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def fail_if_called(**kwargs):
        raise AssertionError("OpenAI client should not be constructed without an API key")

    monkeypatch.setattr(openai_api, "OpenAI", fail_if_called)

    with pytest.raises(SummarizationError, match="OPENAI_API_KEY"):
        openai_api.summarize(sample_input)


def test_summarize_api_failure_raises_summarization_error(monkeypatch, sample_input):
    class BoomCompletions:
        def create(self, **kwargs):
            raise RuntimeError("network boom")

    class BoomChat:
        completions = BoomCompletions()

    class BoomClient:
        chat = BoomChat()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(openai_api, "OpenAI", lambda api_key: BoomClient())

    with pytest.raises(SummarizationError, match="network boom"):
        openai_api.summarize(sample_input)
