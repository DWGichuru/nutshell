import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from backend import db
from backend.models import VideoMeta


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "index.db"


def make_meta(video_id: str, **overrides) -> VideoMeta:
    defaults = dict(
        video_id=video_id,
        title="Test Video",
        channel="Test Channel",
        duration_seconds=120,
        date_added=datetime.now(UTC).isoformat(),
        source_url=f"https://youtu.be/{video_id}",
    )
    defaults.update(overrides)
    return VideoMeta(**defaults)


def test_init_db_creates_file_and_table(db_path):
    db.init_db(db_path)

    assert db_path.exists()
    conn = db.get_connection(db_path)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(videos)")}
    finally:
        conn.close()
    assert columns == {"video_id", "title", "channel", "duration_seconds", "date_added", "path"}


def test_init_db_is_idempotent(db_path):
    db.init_db(db_path)
    db.init_db(db_path)

    assert db_path.exists()


def _fetch_video(db_path, video_id):
    conn = db.get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT video_id, title, channel, duration_seconds, date_added, path FROM videos WHERE video_id = ?",
            (video_id,),
        ).fetchone()
    finally:
        conn.close()
    return row


def test_upsert_video_inserts_new_row(db_path):
    db.init_db(db_path)
    meta = make_meta("abc123", title="First Title")

    db.upsert_video(meta, Path("/data/videos/abc123"), db_path)

    row = _fetch_video(db_path, "abc123")
    assert row == (
        "abc123",
        "First Title",
        "Test Channel",
        120,
        meta.date_added,
        "/data/videos/abc123",
    )


def test_upsert_video_updates_existing_row_in_place(db_path):
    db.init_db(db_path)
    db.upsert_video(make_meta("abc123", title="Old Title"), Path("/data/videos/abc123"), db_path)

    updated_meta = make_meta("abc123", title="New Title", duration_seconds=999)
    db.upsert_video(updated_meta, Path("/data/videos/abc123"), db_path)

    conn = db.get_connection(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    finally:
        conn.close()
    assert count == 1

    row = _fetch_video(db_path, "abc123")
    assert row[1] == "New Title"
    assert row[3] == 999


def _write_meta_fixture(data_root: Path, meta: VideoMeta) -> None:
    video_dir = data_root / meta.video_id
    video_dir.mkdir(parents=True, exist_ok=True)
    (video_dir / "meta.json").write_text(meta.model_dump_json())


def test_rebuild_index_populates_from_meta_json_files(db_path, tmp_path):
    data_root = tmp_path / "videos"
    _write_meta_fixture(data_root, make_meta("abc123", title="First"))
    _write_meta_fixture(data_root, make_meta("def456", title="Second"))

    count = db.rebuild_index(data_root, db_path)

    assert count == 2
    row = _fetch_video(db_path, "abc123")
    assert row[1] == "First"
    assert row[5] == str(data_root / "abc123")
    row = _fetch_video(db_path, "def456")
    assert row[1] == "Second"


def test_rebuild_index_drops_stale_rows_no_longer_on_disk(db_path, tmp_path):
    data_root = tmp_path / "videos"
    _write_meta_fixture(data_root, make_meta("abc123"))
    db.rebuild_index(data_root, db_path)

    # abc123's folder is gone and a new video appears before the next rebuild.
    shutil.rmtree(data_root / "abc123")
    _write_meta_fixture(data_root, make_meta("ghi789"))

    count = db.rebuild_index(data_root, db_path)

    assert count == 1
    assert _fetch_video(db_path, "abc123") is None
    assert _fetch_video(db_path, "ghi789") is not None
