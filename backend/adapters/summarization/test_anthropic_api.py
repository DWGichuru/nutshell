import anthropic
import httpx
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


def test_summarize_returns_response_text(monkeypatch, sample_input):
    response = FakeMessage(content=[FakeTextBlock(text="# summary")])
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(anthropic_api, "Anthropic", lambda api_key: FakeAnthropic(response=response))

    result = anthropic_api.summarize(sample_input)

    assert result == "# summary"


def test_summarize_includes_timestamps_when_segments_present(monkeypatch, sample_input):
    captured = {}

    class CapturingMessages:
        def create(self, **kwargs):
            captured["prompt"] = kwargs["messages"][0]["content"]
            return FakeMessage(content=[FakeTextBlock(text="ok")])

    class CapturingClient:
        messages = CapturingMessages()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(anthropic_api, "Anthropic", lambda api_key: CapturingClient())

    anthropic_api.summarize(sample_input)

    assert "1:05" in captured["prompt"]


def test_summarize_falls_back_to_plain_text_without_segments(monkeypatch):
    input_without_segments = SummaryInput(text="hello world, this is a test transcript.", segments=[])
    captured = {}

    class CapturingMessages:
        def create(self, **kwargs):
            captured["prompt"] = kwargs["messages"][0]["content"]
            return FakeMessage(content=[FakeTextBlock(text="ok")])

    class CapturingClient:
        messages = CapturingMessages()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(anthropic_api, "Anthropic", lambda api_key: CapturingClient())

    anthropic_api.summarize(input_without_segments)

    assert "hello world, this is a test transcript." in captured["prompt"]


def test_summarize_missing_api_key_raises_before_client(monkeypatch, sample_input):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def fail_if_called(**kwargs):
        raise AssertionError("Anthropic client should not be constructed without an API key")

    monkeypatch.setattr(anthropic_api, "Anthropic", fail_if_called)

    with pytest.raises(SummarizationError, match="ANTHROPIC_API_KEY"):
        anthropic_api.summarize(sample_input)


def test_summarize_invalid_api_key_raises_friendly_message(monkeypatch, sample_input):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(status_code=401, request=request)

    class UnauthorizedMessages:
        def create(self, **kwargs):
            raise anthropic.AuthenticationError("invalid x-api-key", response=response, body=None)

    class UnauthorizedClient:
        messages = UnauthorizedMessages()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "bad-key")
    monkeypatch.setattr(anthropic_api, "Anthropic", lambda api_key: UnauthorizedClient())

    with pytest.raises(SummarizationError, match="Invalid Anthropic API key"):
        anthropic_api.summarize(sample_input)


def test_summarize_api_failure_raises_summarization_error(monkeypatch, sample_input):
    class BoomMessages:
        def create(self, **kwargs):
            raise RuntimeError("network boom")

    class BoomClient:
        messages = BoomMessages()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(anthropic_api, "Anthropic", lambda api_key: BoomClient())

    with pytest.raises(SummarizationError, match="network boom"):
        anthropic_api.summarize(sample_input)
