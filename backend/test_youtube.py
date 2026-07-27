from unittest.mock import MagicMock

import pytest

from backend import youtube


def test_convert_to_mp3_skips_conversion_when_already_mp3(tmp_path):
    src = tmp_path / "audio.mp3"
    src.write_bytes(b"fake")

    result = youtube.convert_to_mp3(src)

    assert result == src
    assert src.exists()


def test_convert_to_mp3_converts_and_removes_source(tmp_path, monkeypatch):
    src = tmp_path / "audio.webm"
    src.write_bytes(b"fake")

    def fake_run(cmd, check, capture_output):
        (tmp_path / "audio.mp3").write_bytes(b"converted")
        return MagicMock()

    monkeypatch.setattr(youtube.subprocess, "run", fake_run)

    result = youtube.convert_to_mp3(src)

    assert result == tmp_path / "audio.mp3"
    assert result.exists()
    assert not src.exists()


def test_convert_to_mp3_raises_youtube_error_on_ffmpeg_failure(tmp_path, monkeypatch):
    src = tmp_path / "audio.webm"
    src.write_bytes(b"fake")

    def fake_run(cmd, check, capture_output):
        raise youtube.subprocess.CalledProcessError(1, cmd, stderr=b"boom")

    monkeypatch.setattr(youtube.subprocess, "run", fake_run)

    with pytest.raises(youtube.YouTubeError):
        youtube.convert_to_mp3(src)

    assert src.exists()


def test_trim_audio_replaces_source_with_trimmed_output(tmp_path, monkeypatch):
    src = tmp_path / "audio.mp3"
    src.write_bytes(b"original")

    captured_cmd = []

    def fake_run(cmd, check, capture_output):
        captured_cmd.extend(cmd)
        (tmp_path / "audio.trimmed.mp3").write_bytes(b"trimmed")
        return MagicMock()

    monkeypatch.setattr(youtube.subprocess, "run", fake_run)

    result = youtube.trim_audio(src, 10.0, 20.0)

    assert result == src
    assert src.read_bytes() == b"trimmed"
    assert "-ss" in captured_cmd
    assert "10.0" in captured_cmd
    assert "-to" in captured_cmd
    assert "20.0" in captured_cmd


def test_trim_audio_raises_youtube_error_on_ffmpeg_failure(tmp_path, monkeypatch):
    src = tmp_path / "audio.mp3"
    src.write_bytes(b"original")

    def fake_run(cmd, check, capture_output):
        raise youtube.subprocess.CalledProcessError(1, cmd, stderr=b"boom")

    monkeypatch.setattr(youtube.subprocess, "run", fake_run)

    with pytest.raises(youtube.YouTubeError):
        youtube.trim_audio(src, 10.0, 20.0)

    assert src.read_bytes() == b"original"


class _FakeYDL:
    """Stands in for yt_dlp.YoutubeDL: instantiated with opts, used as a context manager."""

    def __init__(self, extract_info_result=None, extract_info_error=None):
        self._extract_info_result = extract_info_result
        self._extract_info_error = extract_info_error
        self.opts = None

    def __call__(self, opts):
        self.opts = opts
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def extract_info(self, url, download):
        if self._extract_info_error:
            raise self._extract_info_error
        return self._extract_info_result

    def prepare_filename(self, info):
        return self.opts["outtmpl"].replace("%(ext)s", info["ext"])


def test_download_audio_returns_downloaded_path(tmp_path, monkeypatch):
    monkeypatch.setattr(youtube.yt_dlp, "YoutubeDL", _FakeYDL(extract_info_result={"id": "abc123", "ext": "webm"}))

    result = youtube.download_audio("https://youtu.be/abc123", tmp_path)

    assert result == tmp_path / "audio.webm"


def test_download_audio_raises_youtube_error_on_download_error(tmp_path, monkeypatch):
    monkeypatch.setattr(
        youtube.yt_dlp, "YoutubeDL", _FakeYDL(extract_info_error=youtube.yt_dlp.utils.DownloadError("boom"))
    )

    with pytest.raises(youtube.YouTubeError):
        youtube.download_audio("https://youtu.be/bad", tmp_path)
