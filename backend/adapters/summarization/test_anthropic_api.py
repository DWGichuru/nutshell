import pytest

from backend.adapters.summarization import anthropic_api
from backend.adapters.summarization.base import SummarizationError, SummaryInput
from backend.adapters.summarization.fakes import FakeAnthropic, FakeMessage, FakeTextBlock
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


@pytest.mark.parametrize("format", ["paragraph", "bullets", "chaptered"])
def test_summarize_returns_response_text(monkeypatch, sample_input, format):
    response = FakeMessage(content=[FakeTextBlock(text=f"# {format} summary")])
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(anthropic_api, "Anthropic", lambda api_key: FakeAnthropic(response=response))

    result = anthropic_api.summarize(sample_input, format)

    assert result == f"# {format} summary"


def test_summarize_chaptered_includes_timestamps_in_prompt(monkeypatch, sample_input):
    captured = {}

    class CapturingMessages:
        def create(self, **kwargs):
            captured["prompt"] = kwargs["messages"][0]["content"]
            return FakeMessage(content=[FakeTextBlock(text="ok")])

    class CapturingClient:
        messages = CapturingMessages()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(anthropic_api, "Anthropic", lambda api_key: CapturingClient())

    anthropic_api.summarize(sample_input, "chaptered")

    assert "1:05" in captured["prompt"]


def test_summarize_missing_api_key_raises_before_client(monkeypatch, sample_input):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def fail_if_called(**kwargs):
        raise AssertionError("Anthropic client should not be constructed without an API key")

    monkeypatch.setattr(anthropic_api, "Anthropic", fail_if_called)

    with pytest.raises(SummarizationError, match="ANTHROPIC_API_KEY"):
        anthropic_api.summarize(sample_input, "paragraph")


def test_summarize_api_failure_raises_summarization_error(monkeypatch, sample_input):
    class BoomMessages:
        def create(self, **kwargs):
            raise RuntimeError("network boom")

    class BoomClient:
        messages = BoomMessages()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(anthropic_api, "Anthropic", lambda api_key: BoomClient())

    with pytest.raises(SummarizationError, match="network boom"):
        anthropic_api.summarize(sample_input, "paragraph")
