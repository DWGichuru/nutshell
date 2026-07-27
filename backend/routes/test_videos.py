import json

import pytest
from fastapi.testclient import TestClient

from backend import db, storage
from backend.main import app
from backend.models import VideoMeta
from backend.routes.videos import estimate_transcription
from backend.youtube import YouTubeError

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_data_root(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_ROOT", tmp_path / "videos")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "index.db")
    db.init_db()


@pytest.mark.parametrize(
    "duration_seconds,expected_needs_confirmation,expected_estimate",
    [
        (0, False, None),
        (3600, False, None),
        (3601, True, 30.0),
        (7200, True, 60.0),
    ],
)
def test_estimate_transcription(duration_seconds, expected_needs_confirmation, expected_estimate):
    needs_confirmation, estimated_minutes = estimate_transcription(duration_seconds)
    assert needs_confirmation is expected_needs_confirmation
    assert estimated_minutes == expected_estimate


def test_get_metadata_success(monkeypatch):
    def fake_fetch_metadata(url):
        return {"title": "Test Video", "channel": "Test Channel", "duration": 120}

    monkeypatch.setattr("backend.routes.videos.fetch_metadata", fake_fetch_metadata)

    response = client.post("/api/videos/metadata", json={"url": "https://youtu.be/fake"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Test Video"
    assert body["channel"] == "Test Channel"
    assert body["duration_seconds"] == 120
    assert body["needs_confirmation"] is False
    assert body["estimated_minutes"] is None


def test_get_metadata_long_video_needs_confirmation(monkeypatch):
    def fake_fetch_metadata(url):
        return {"title": "Long Video", "channel": "Test Channel", "duration": 7200}

    monkeypatch.setattr("backend.routes.videos.fetch_metadata", fake_fetch_metadata)

    response = client.post("/api/videos/metadata", json={"url": "https://youtu.be/fake"})

    assert response.status_code == 200
    body = response.json()
    assert body["needs_confirmation"] is True
    assert body["estimated_minutes"] == 60.0


def test_get_metadata_invalid_url(monkeypatch):
    def fake_fetch_metadata(url):
        raise YouTubeError("Unable to extract video data")

    monkeypatch.setattr("backend.routes.videos.fetch_metadata", fake_fetch_metadata)

    response = client.post("/api/videos/metadata", json={"url": "not-a-real-url"})

    assert response.status_code == 400
    assert "Unable to extract video data" in response.json()["detail"]


def test_start_download_and_status_success(monkeypatch, tmp_path):
    def fake_fetch_metadata(url):
        return {"id": "abc123", "title": "Test Video", "channel": "Test Channel", "duration": 42}

    def fake_download_audio(url, dest_dir):
        path = dest_dir / "audio.webm"
        path.write_bytes(b"fake")
        return path

    def fake_convert_to_mp3(src_path):
        dest = src_path.with_suffix(".mp3")
        src_path.rename(dest)
        return dest

    monkeypatch.setattr("backend.routes.videos.fetch_metadata", fake_fetch_metadata)
    monkeypatch.setattr("backend.routes.videos.download_audio", fake_download_audio)
    monkeypatch.setattr("backend.routes.videos.convert_to_mp3", fake_convert_to_mp3)

    response = client.post("/api/videos/download", json={"url": "https://youtu.be/abc123"})

    assert response.status_code == 200
    body = response.json()
    assert body["video_id"] == "abc123"
    assert body["status"] == "pending"

    status_response = client.get("/api/videos/abc123/status")
    assert status_response.status_code == 200
    assert status_response.json() == {"status": "done", "error": None}

    video_dir = tmp_path / "videos" / "abc123"
    assert (video_dir / "audio.mp3").exists()
    meta = (video_dir / "meta.json").read_text()
    assert '"video_id":"abc123"' in meta.replace(" ", "").replace("\n", "")

    conn = db.get_connection(tmp_path / "index.db")
    try:
        row = conn.execute(
            "SELECT video_id, title, channel, duration_seconds, path FROM videos WHERE video_id = ?",
            ("abc123",),
        ).fetchone()
    finally:
        conn.close()
    assert row == ("abc123", "Test Video", "Test Channel", 42, str(video_dir))


def test_start_download_failure_sets_error_status(monkeypatch):
    def fake_fetch_metadata(url):
        return {"id": "badvid", "title": "Bad Video", "channel": "Test Channel", "duration": 10}

    def fake_download_audio(url, dest_dir):
        raise YouTubeError("network boom")

    monkeypatch.setattr("backend.routes.videos.fetch_metadata", fake_fetch_metadata)
    monkeypatch.setattr("backend.routes.videos.download_audio", fake_download_audio)

    response = client.post("/api/videos/download", json={"url": "https://youtu.be/badvid"})
    assert response.status_code == 200

    status_response = client.get("/api/videos/badvid/status")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "error"
    assert "network boom" in status_response.json()["error"]


def test_start_download_unexpected_failure_sets_error_status(monkeypatch):
    def fake_fetch_metadata(url):
        return {"id": "diskfail", "title": "Disk Fail Video", "channel": "Test Channel", "duration": 10}

    def fake_download_audio(url, dest_dir):
        raise OSError("disk full")

    monkeypatch.setattr("backend.routes.videos.fetch_metadata", fake_fetch_metadata)
    monkeypatch.setattr("backend.routes.videos.download_audio", fake_download_audio)

    response = client.post("/api/videos/download", json={"url": "https://youtu.be/diskfail"})
    assert response.status_code == 200

    status_response = client.get("/api/videos/diskfail/status")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "error"
    assert "disk full" in status_response.json()["error"]


def test_start_download_invalid_url(monkeypatch):
    def fake_fetch_metadata(url):
        raise YouTubeError("Unable to extract video data")

    monkeypatch.setattr("backend.routes.videos.fetch_metadata", fake_fetch_metadata)

    response = client.post("/api/videos/download", json={"url": "not-a-real-url"})

    assert response.status_code == 400


def test_get_status_unknown_video_id_returns_404():
    response = client.get("/api/videos/does-not-exist/status")

    assert response.status_code == 404


def test_get_audio_returns_file_when_present(tmp_path):
    video_dir = tmp_path / "videos" / "abc123"
    video_dir.mkdir(parents=True)
    (video_dir / "audio.mp3").write_bytes(b"fake-audio-bytes")

    response = client.get("/api/videos/abc123/audio")

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == b"fake-audio-bytes"


def test_get_audio_unknown_video_id_returns_404():
    response = client.get("/api/videos/does-not-exist/audio")

    assert response.status_code == 404


def _write_video(tmp_path, video_id, duration_seconds=60):
    video_dir = tmp_path / "videos" / video_id
    video_dir.mkdir(parents=True)
    (video_dir / "audio.mp3").write_bytes(b"original-audio")
    meta = {
        "video_id": video_id,
        "title": "Test Video",
        "channel": "Test Channel",
        "duration_seconds": duration_seconds,
        "date_added": "2026-01-01T00:00:00+00:00",
        "source_url": "https://youtu.be/fake",
    }
    (video_dir / "meta.json").write_text(json.dumps(meta))
    return video_dir


def test_trim_success(tmp_path, monkeypatch):
    video_dir = _write_video(tmp_path, "abc123")

    def fake_trim_audio(src_path, start_seconds, end_seconds):
        src_path.write_bytes(b"trimmed-audio")
        return src_path

    monkeypatch.setattr("backend.routes.videos.trim_audio", fake_trim_audio)

    response = client.post("/api/videos/abc123/trim", json={"start_seconds": 5.0, "end_seconds": 15.0})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "trimmed"
    assert body["duration_seconds"] == 10.0
    assert (video_dir / "audio.mp3").read_bytes() == b"trimmed-audio"


def test_trim_invalid_range_returns_400(tmp_path):
    _write_video(tmp_path, "abc123")

    response = client.post("/api/videos/abc123/trim", json={"start_seconds": 15.0, "end_seconds": 5.0})

    assert response.status_code == 400


def test_trim_end_exceeds_duration_returns_400(tmp_path):
    _write_video(tmp_path, "abc123", duration_seconds=30)

    response = client.post("/api/videos/abc123/trim", json={"start_seconds": 0.0, "end_seconds": 60.0})

    assert response.status_code == 400


def test_trim_unknown_video_id_returns_404():
    response = client.post("/api/videos/does-not-exist/trim", json={"start_seconds": 0.0, "end_seconds": 10.0})

    assert response.status_code == 404


def test_transcribe_api_success(monkeypatch, tmp_path):
    from backend.adapters.transcription.base import TranscriptResult, TranscriptSegment

    _write_video(tmp_path, "abc123")

    def fake_transcribe(audio_path):
        return TranscriptResult(
            text="hello world",
            segments=[TranscriptSegment(start=0.0, end=1.5, text="hello world")],
            method="api",
        )

    monkeypatch.setattr("backend.routes.videos.transcribe_api", fake_transcribe)

    response = client.post("/api/videos/abc123/transcribe", json={"method": "api"})

    assert response.status_code == 200
    body = response.json()
    assert body["video_id"] == "abc123"
    assert body["status"] == "pending"

    status_response = client.get("/api/videos/abc123/transcription/status")
    assert status_response.status_code == 200
    assert status_response.json() == {"status": "done", "error": None}

    transcript_response = client.get("/api/videos/abc123/transcript")
    assert transcript_response.status_code == 200
    transcript_body = transcript_response.json()
    assert transcript_body["text"] == "hello world"
    assert transcript_body["method"] == "api"
    assert transcript_body["segments"] == [{"start": 0.0, "end": 1.5, "text": "hello world"}]

    saved = (tmp_path / "videos" / "abc123" / "transcript.json").read_text()
    assert '"method":"api"' in saved.replace(" ", "").replace("\n", "")


def test_transcribe_local_success(monkeypatch, tmp_path):
    from backend.adapters.transcription.base import TranscriptResult, TranscriptSegment

    _write_video(tmp_path, "abc123")

    def fake_transcribe(audio_path):
        return TranscriptResult(
            text="hello from local",
            segments=[TranscriptSegment(start=0.0, end=2.0, text="hello from local")],
            method="local",
        )

    monkeypatch.setattr("backend.routes.videos.transcribe_local", fake_transcribe)

    response = client.post("/api/videos/abc123/transcribe", json={"method": "local"})

    assert response.status_code == 200

    status_response = client.get("/api/videos/abc123/transcription/status")
    assert status_response.status_code == 200
    assert status_response.json() == {"status": "done", "error": None}

    transcript_response = client.get("/api/videos/abc123/transcript")
    assert transcript_response.status_code == 200
    transcript_body = transcript_response.json()
    assert transcript_body["text"] == "hello from local"
    assert transcript_body["method"] == "local"


def test_transcribe_failure_sets_error_status(monkeypatch, tmp_path):
    _write_video(tmp_path, "abc123")

    def fake_transcribe(audio_path):
        raise RuntimeError("api boom")

    monkeypatch.setattr("backend.routes.videos.transcribe_api", fake_transcribe)

    response = client.post("/api/videos/abc123/transcribe", json={"method": "api"})
    assert response.status_code == 200

    status_response = client.get("/api/videos/abc123/transcription/status")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "error"
    assert "api boom" in status_response.json()["error"]


def test_transcribe_unknown_video_id_returns_404():
    response = client.post("/api/videos/does-not-exist/transcribe", json={"method": "api"})

    assert response.status_code == 404


def test_get_transcription_status_unknown_video_id_returns_404():
    response = client.get("/api/videos/does-not-exist/transcription/status")

    assert response.status_code == 404


def test_get_transcript_unknown_video_id_returns_404():
    response = client.get("/api/videos/does-not-exist/transcript")

    assert response.status_code == 404


def _write_transcript(tmp_path, video_id, text="hello world"):
    video_dir = tmp_path / "videos" / video_id
    video_dir.mkdir(parents=True, exist_ok=True)
    transcript = {
        "text": text,
        "segments": [{"start": 0.0, "end": 1.5, "text": text}],
        "method": "api",
    }
    (video_dir / "transcript.json").write_text(json.dumps(transcript))


def test_summarize_success(monkeypatch, tmp_path):
    _write_video(tmp_path, "abc123")
    _write_transcript(tmp_path, "abc123")

    def fake_summarize(input, format):
        return f"# {format} summary"

    monkeypatch.setattr("backend.routes.videos.summarize_anthropic", fake_summarize)

    response = client.post("/api/videos/abc123/summarize", json={"format": "bullets"})

    assert response.status_code == 200
    body = response.json()
    assert body["video_id"] == "abc123"
    assert body["status"] == "pending"

    status_response = client.get("/api/videos/abc123/summarization/status")
    assert status_response.status_code == 200
    assert status_response.json() == {"status": "done", "error": None}

    list_response = client.get("/api/videos/abc123/summaries")
    assert list_response.status_code == 200
    summaries = list_response.json()["summaries"]
    assert len(summaries) == 1
    assert summaries[0]["format"] == "bullets"
    assert summaries[0]["content"] == "# bullets summary"


def test_summarize_openai_provider_success(monkeypatch, tmp_path):
    _write_video(tmp_path, "abc123")
    _write_transcript(tmp_path, "abc123")

    def fake_summarize(input, format):
        return f"# openai {format} summary"

    monkeypatch.setattr("backend.routes.videos.summarize_openai", fake_summarize)

    response = client.post("/api/videos/abc123/summarize", json={"format": "paragraph", "provider": "openai"})

    assert response.status_code == 200

    status_response = client.get("/api/videos/abc123/summarization/status")
    assert status_response.json() == {"status": "done", "error": None}

    list_response = client.get("/api/videos/abc123/summaries")
    summaries = list_response.json()["summaries"]
    assert summaries[0]["content"] == "# openai paragraph summary"


def test_summarize_unknown_transcript_returns_404(tmp_path):
    _write_video(tmp_path, "abc123")

    response = client.post("/api/videos/abc123/summarize", json={"format": "paragraph"})

    assert response.status_code == 404


def test_summarize_failure_sets_error_status(monkeypatch, tmp_path):
    _write_video(tmp_path, "abc123")
    _write_transcript(tmp_path, "abc123")

    def fake_summarize(input, format):
        raise RuntimeError("anthropic boom")

    monkeypatch.setattr("backend.routes.videos.summarize_anthropic", fake_summarize)

    response = client.post("/api/videos/abc123/summarize", json={"format": "paragraph"})
    assert response.status_code == 200

    status_response = client.get("/api/videos/abc123/summarization/status")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "error"
    assert "anthropic boom" in status_response.json()["error"]


def test_get_summarization_status_unknown_video_id_returns_404():
    response = client.get("/api/videos/does-not-exist/summarization/status")

    assert response.status_code == 404


def test_get_summaries_unknown_video_id_returns_404():
    response = client.get("/api/videos/does-not-exist/summaries")

    assert response.status_code == 404


def _seed_video(tmp_path, video_id, **overrides):
    video_dir = _write_video(tmp_path, video_id)
    meta_dict = json.loads((video_dir / "meta.json").read_text())
    meta_dict.update(overrides)
    (video_dir / "meta.json").write_text(json.dumps(meta_dict))
    meta = VideoMeta(**meta_dict)
    db.upsert_video(meta, video_dir)
    return meta


def test_get_videos_returns_empty_list_when_no_videos():
    response = client.get("/api/videos")

    assert response.status_code == 200
    assert response.json() == {"videos": []}


def test_get_videos_returns_all_videos(tmp_path):
    _seed_video(tmp_path, "abc123", title="First")
    _seed_video(tmp_path, "def456", title="Second")

    response = client.get("/api/videos")

    assert response.status_code == 200
    video_ids = {video["video_id"] for video in response.json()["videos"]}
    assert video_ids == {"abc123", "def456"}


def test_get_videos_search_filters_by_title(tmp_path):
    _seed_video(tmp_path, "abc123", title="Deep Dive Into Rust")
    _seed_video(tmp_path, "def456", title="Cooking Basics")

    response = client.get("/api/videos", params={"search": "rust"})

    assert response.status_code == 200
    videos = response.json()["videos"]
    assert [video["video_id"] for video in videos] == ["abc123"]


def test_get_videos_date_range_filters_results(tmp_path):
    _seed_video(tmp_path, "jan", date_added="2026-01-15T00:00:00+00:00")
    _seed_video(tmp_path, "jun", date_added="2026-06-15T00:00:00+00:00")

    response = client.get("/api/videos", params={"date_from": "2026-05-01"})

    assert response.status_code == 200
    videos = response.json()["videos"]
    assert [video["video_id"] for video in videos] == ["jun"]


def test_get_video_returns_meta(tmp_path):
    _seed_video(tmp_path, "abc123", title="Some Title")

    response = client.get("/api/videos/abc123")

    assert response.status_code == 200
    body = response.json()
    assert body["video_id"] == "abc123"
    assert body["title"] == "Some Title"


def test_get_video_unknown_video_id_returns_404():
    response = client.get("/api/videos/does-not-exist")

    assert response.status_code == 404
