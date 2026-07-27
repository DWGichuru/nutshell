import pytest
from fastapi.testclient import TestClient

from backend import storage
from backend.main import app
from backend.routes.videos import estimate_transcription
from backend.youtube import YouTubeError

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_data_root(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_ROOT", tmp_path / "videos")


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
