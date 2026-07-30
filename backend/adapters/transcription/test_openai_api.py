import httpx
import openai
import pytest

from backend.adapters.transcription import openai_api
from backend.adapters.transcription.base import TranscriptionError
from backend.adapters.transcription.fakes import FakeOpenAI, FakeSegment, FakeTranscription


def test_transcribe_maps_response_to_transcript_result(monkeypatch, tmp_path):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake-audio")
    response = FakeTranscription(
        text="hello world",
        segments=[FakeSegment(start=0.0, end=1.5, text="hello world")],
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(openai_api, "OpenAI", lambda api_key: FakeOpenAI(response=response))

    result = openai_api.transcribe(audio_path)

    assert result.text == "hello world"
    assert result.method == "api"
    assert len(result.segments) == 1
    assert result.segments[0].start == 0.0
    assert result.segments[0].end == 1.5
    assert result.segments[0].text == "hello world"


def test_transcribe_missing_api_key_raises_before_client(monkeypatch, tmp_path):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake-audio")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def fail_if_called(**kwargs):
        raise AssertionError("OpenAI client should not be constructed without an API key")

    monkeypatch.setattr(openai_api, "OpenAI", fail_if_called)

    with pytest.raises(TranscriptionError, match="OPENAI_API_KEY"):
        openai_api.transcribe(audio_path)


def test_transcribe_invalid_api_key_raises_friendly_message(monkeypatch, tmp_path):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake-audio")
    request = httpx.Request("POST", "https://api.openai.com/v1/audio/transcriptions")
    response = httpx.Response(status_code=401, request=request)

    class UnauthorizedTranscriptions:
        def create(self, **kwargs):
            raise openai.AuthenticationError("Incorrect API key provided", response=response, body=None)

    class UnauthorizedAudio:
        transcriptions = UnauthorizedTranscriptions()

    class UnauthorizedClient:
        audio = UnauthorizedAudio()

    monkeypatch.setenv("OPENAI_API_KEY", "bad-key")
    monkeypatch.setattr(openai_api, "OpenAI", lambda api_key: UnauthorizedClient())

    with pytest.raises(TranscriptionError, match="Invalid OpenAI API key"):
        openai_api.transcribe(audio_path)


def test_transcribe_api_failure_raises_transcription_error(monkeypatch, tmp_path):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake-audio")

    class BoomTranscriptions:
        def create(self, **kwargs):
            raise RuntimeError("network boom")

    class BoomAudio:
        transcriptions = BoomTranscriptions()

    class BoomClient:
        audio = BoomAudio()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(openai_api, "OpenAI", lambda api_key: BoomClient())

    with pytest.raises(TranscriptionError, match="network boom"):
        openai_api.transcribe(audio_path)
