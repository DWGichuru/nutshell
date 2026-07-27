from backend.adapters.transcription import local_mlx, openai_api
from backend.adapters.transcription.fakes import FakeOpenAI, FakeSegment, FakeTranscription

FIXTURE_TEXT = "hello world"
FIXTURE_SEGMENT = {"start": 0.0, "end": 1.5, "text": FIXTURE_TEXT}


def test_both_adapters_produce_consistent_transcript_shape(monkeypatch, tmp_path):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake-audio")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    api_response = FakeTranscription(text=FIXTURE_TEXT, segments=[FakeSegment(**FIXTURE_SEGMENT)])
    monkeypatch.setattr(openai_api, "OpenAI", lambda api_key: FakeOpenAI(response=api_response))

    local_response = {"text": FIXTURE_TEXT, "segments": [FIXTURE_SEGMENT]}
    monkeypatch.setattr(local_mlx.mlx_whisper, "transcribe", lambda path, path_or_hf_repo: local_response)

    api_result = openai_api.transcribe(audio_path)
    local_result = local_mlx.transcribe(audio_path)

    assert api_result.text == local_result.text == FIXTURE_TEXT
    assert len(api_result.segments) == len(local_result.segments) == 1
    for segment in (api_result.segments[0], local_result.segments[0]):
        assert segment.start == FIXTURE_SEGMENT["start"]
        assert segment.end == FIXTURE_SEGMENT["end"]
        assert segment.text == FIXTURE_SEGMENT["text"]

    assert api_result.method == "api"
    assert local_result.method == "local"
