from datetime import UTC, datetime

import pytest

from backend import storage
from backend.models import Transcript, TranscriptSegmentModel, VideoMeta


@pytest.fixture(autouse=True)
def isolated_data_root(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_ROOT", tmp_path / "videos")


def test_derive_video_id_lowercases_youtube_id():
    assert storage.derive_video_id({"id": "AbC123"}) == "abc123"


def test_video_dir_creates_folder():
    path = storage.video_dir("abc123")
    assert path.is_dir()
    assert path.name == "abc123"


def test_write_and_read_meta_round_trip():
    meta = VideoMeta(
        video_id="abc123",
        title="Test Video",
        channel="Test Channel",
        duration_seconds=120,
        date_added=datetime.now(UTC).isoformat(),
        source_url="https://youtu.be/abc123",
    )

    storage.write_meta("abc123", meta)
    loaded = storage.read_meta("abc123")

    assert loaded == meta
    assert (storage.DATA_ROOT / "abc123" / "meta.json").exists()


def test_write_and_read_transcript_round_trip():
    storage.video_dir("abc123")
    transcript = Transcript(
        text="hello world",
        segments=[TranscriptSegmentModel(start=0.0, end=1.5, text="hello world")],
        method="api",
    )

    storage.write_transcript("abc123", transcript)
    loaded = storage.read_transcript("abc123")

    assert loaded == transcript
    assert (storage.DATA_ROOT / "abc123" / "transcript.json").exists()
