import sqlite3
from pathlib import Path

from backend import storage
from backend.models import VideoMeta

DB_PATH = Path("data/index.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    channel TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    date_added TEXT NOT NULL,
    path TEXT NOT NULL
)
"""


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    return sqlite3.connect(db_path if db_path is not None else DB_PATH)


def init_db(db_path: Path | None = None) -> None:
    if db_path is None:
        db_path = DB_PATH

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(db_path)
    try:
        conn.execute(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def upsert_video(meta: VideoMeta, path: Path, db_path: Path | None = None) -> None:
    conn = get_connection(db_path)
    try:
        conn.execute(
            """
            INSERT INTO videos (video_id, title, channel, duration_seconds, date_added, path)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                title = excluded.title,
                channel = excluded.channel,
                duration_seconds = excluded.duration_seconds,
                date_added = excluded.date_added,
                path = excluded.path
            """,
            (meta.video_id, meta.title, meta.channel, meta.duration_seconds, meta.date_added, str(path)),
        )
        conn.commit()
    finally:
        conn.close()


def rebuild_index(data_root: Path | None = None, db_path: Path | None = None) -> int:
    if data_root is None:
        data_root = storage.DATA_ROOT
    if db_path is None:
        db_path = DB_PATH

    init_db(db_path)
    conn = get_connection(db_path)
    try:
        conn.execute("DELETE FROM videos")
        count = 0
        for meta_path in sorted(data_root.glob("*/meta.json")):
            meta = VideoMeta.model_validate_json(meta_path.read_text())
            conn.execute(
                """
                INSERT INTO videos (video_id, title, channel, duration_seconds, date_added, path)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (meta.video_id, meta.title, meta.channel, meta.duration_seconds, meta.date_added, str(meta_path.parent)),
            )
            count += 1
        conn.commit()
        return count
    finally:
        conn.close()
