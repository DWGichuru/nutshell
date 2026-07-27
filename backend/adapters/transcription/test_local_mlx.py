import pytest

from backend.adapters.transcription import local_mlx
from backend.adapters.transcription.base import TranscriptionError


def test_transcribe_maps_response_to_transcript_result(monkeypatch, tmp_path):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake-audio")
    fake_result = {
        "text": "hello world",
        "segments": [{"start": 0.0, "end": 1.5, "text": "hello world"}],
    }

    def fake_transcribe(path, path_or_hf_repo):
        assert path == str(audio_path)
        assert path_or_hf_repo == local_mlx.MODEL
        return fake_result

    monkeypatch.setattr(local_mlx.mlx_whisper, "transcribe", fake_transcribe)

    result = local_mlx.transcribe(audio_path)

    assert result.text == "hello world"
    assert result.method == "local"
    assert len(result.segments) == 1
    assert result.segments[0].start == 0.0
    assert result.segments[0].end == 1.5
    assert result.segments[0].text == "hello world"


def test_transcribe_failure_raises_transcription_error(monkeypatch, tmp_path):
    audio_path = tmp_path / "audio.mp3"
    audio_path.write_bytes(b"fake-audio")

    def fake_transcribe(path, path_or_hf_repo):
        raise RuntimeError("model load failed")

    monkeypatch.setattr(local_mlx.mlx_whisper, "transcribe", fake_transcribe)

    with pytest.raises(TranscriptionError, match="model load failed"):
        local_mlx.transcribe(audio_path)
