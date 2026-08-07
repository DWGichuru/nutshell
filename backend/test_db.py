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


def test_list_videos_returns_all_with_no_filters(db_path):
    db.init_db(db_path)
    db.upsert_video(make_meta("abc123", title="First"), Path("/data/videos/abc123"), db_path)
    db.upsert_video(make_meta("def456", title="Second"), Path("/data/videos/def456"), db_path)

    rows = db.list_videos(db_path=db_path)

    assert {row[0] for row in rows} == {"abc123", "def456"}


def test_list_videos_orders_by_date_added_descending(db_path):
    db.init_db(db_path)
    db.upsert_video(
        make_meta("older", title="Older", date_added="2026-01-01T00:00:00+00:00"),
        Path("/data/videos/older"),
        db_path,
    )
    db.upsert_video(
        make_meta("newer", title="Newer", date_added="2026-06-01T00:00:00+00:00"),
        Path("/data/videos/newer"),
        db_path,
    )

    rows = db.list_videos(db_path=db_path)

    assert [row[0] for row in rows] == ["newer", "older"]


def test_list_videos_search_matches_title(db_path):
    db.init_db(db_path)
    db.upsert_video(make_meta("abc123", title="Deep Dive Into Rust"), Path("/x"), db_path)
    db.upsert_video(make_meta("def456", title="Cooking Basics"), Path("/y"), db_path)

    rows = db.list_videos(search="rust", db_path=db_path)

    assert [row[0] for row in rows] == ["abc123"]


def test_list_videos_search_matches_channel(db_path):
    db.init_db(db_path)
    db.upsert_video(make_meta("abc123", title="Video A", channel="Tech Channel"), Path("/x"), db_path)
    db.upsert_video(make_meta("def456", title="Video B", channel="Cooking Channel"), Path("/y"), db_path)

    rows = db.list_videos(search="tech", db_path=db_path)

    assert [row[0] for row in rows] == ["abc123"]


def test_list_videos_search_is_case_insensitive(db_path):
    db.init_db(db_path)
    db.upsert_video(make_meta("abc123", title="UPPERCASE TITLE"), Path("/x"), db_path)

    rows = db.list_videos(search="uppercase", db_path=db_path)

    assert [row[0] for row in rows] == ["abc123"]


def test_list_videos_search_escapes_like_wildcards(db_path):
    db.init_db(db_path)
    db.upsert_video(make_meta("abc123", title="100% Done"), Path("/x"), db_path)
    db.upsert_video(make_meta("def456", title="Nothing Related"), Path("/y"), db_path)

    rows = db.list_videos(search="100%", db_path=db_path)

    assert [row[0] for row in rows] == ["abc123"]


def test_list_videos_filters_by_date_range(db_path):
    db.init_db(db_path)
    db.upsert_video(
        make_meta("jan", title="January", date_added="2026-01-15T00:00:00+00:00"),
        Path("/x"),
        db_path,
    )
    db.upsert_video(
        make_meta("mar", title="March", date_added="2026-03-15T00:00:00+00:00"),
        Path("/y"),
        db_path,
    )
    db.upsert_video(
        make_meta("jun", title="June", date_added="2026-06-15T00:00:00+00:00"),
        Path("/z"),
        db_path,
    )

    rows = db.list_videos(date_from="2026-02-01", date_to="2026-05-01", db_path=db_path)

    assert [row[0] for row in rows] == ["mar"]


def test_list_videos_combines_search_and_date_range(db_path):
    db.init_db(db_path)
    db.upsert_video(
        make_meta("early", title="Rust Basics", date_added="2026-01-01T00:00:00+00:00"),
        Path("/x"),
        db_path,
    )
    db.upsert_video(
        make_meta("late", title="Rust Advanced", date_added="2026-06-01T00:00:00+00:00"),
        Path("/y"),
        db_path,
    )

    rows = db.list_videos(search="rust", date_from="2026-05-01", db_path=db_path)

    assert [row[0] for row in rows] == ["late"]


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


def test_resolve_db_path_defaults_to_relative_data_index_db(monkeypatch):
    monkeypatch.delenv("NUTSHELL_DATA_DIR", raising=False)

    assert db._resolve_db_path() == Path("data/index.db")


def test_resolve_db_path_uses_nutshell_data_dir_when_set(monkeypatch):
    monkeypatch.setenv("NUTSHELL_DATA_DIR", "/tmp/nutshell-data")

    assert db._resolve_db_path() == Path("/tmp/nutshell-data/index.db")
