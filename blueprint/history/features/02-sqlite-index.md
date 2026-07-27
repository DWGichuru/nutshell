# Feature: SQLite Index

**From build-plan:** feature 2
**Status:** done

## Goal

Give the app a fast, derived index of every downloaded video so later features
(search, library view) don't need to scan `data/videos/` on every request. The
index is always rebuildable from each video's `meta.json` - it never becomes a
second source of truth.

## In scope

- `videos` table schema in `data/index.db` (video_id, title, channel,
  duration_seconds, date_added, path), matching `project-overview.md`.
- `init_db()` - creates the DB file and table if missing, run on app startup.
- `upsert_video()` - insert or update one index row from a `VideoMeta` + its
  folder path.
- `rebuild_index()` - clears and repopulates the table by scanning
  `data/videos/*/meta.json`.
- Wiring: a successful download upserts its index row immediately, so the
  index stays in sync without a manual rebuild in the common case.

## Out of scope

- Any HTTP endpoint (list, search, manual resync) - that's Phase 6 (library
  view) and Phase 8 (manual resync button). This feature only builds the data
  layer.
- Deleting a video's index row (no delete-video feature yet - Phase 8).

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight on.
   Checkpoints are optional; `/complete` makes the real feature-level commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the step was too big, so split it.

## Build steps

- [x] **Step 1 - DB module: schema + init** - create `backend/db.py` with
  `DB_PATH = Path("data/index.db")`, `get_connection()`, and `init_db()` that
  creates the parent dir and runs `CREATE TABLE IF NOT EXISTS videos (...)`
  matching the schema below. *Done when:* calling `init_db()` against a temp
  path creates the file and a `videos` table with the exact expected columns;
  a test verifies this via `PRAGMA table_info`.
- [x] **Step 2 - upsert_video()** - add `upsert_video(meta: VideoMeta, path:
  Path, db_path: Path = DB_PATH)` using `INSERT ... ON CONFLICT(video_id) DO
  UPDATE`. *Done when:* inserting the same `video_id` twice with different
  field values results in exactly one row reflecting the latest values; a
  test covers both the insert and the update-in-place case.
- [x] **Step 3 - rebuild_index()** - add `rebuild_index(data_root: Path =
  storage.DATA_ROOT, db_path: Path = DB_PATH)` that clears the table and
  re-inserts one row per `data/videos/*/meta.json` found, returning the count
  written. *Done when:* given a temp folder with several `meta.json` fixtures
  (and one stale row from a video no longer on disk), the table after
  rebuild contains exactly the rows matching what's on disk; a test asserts
  this.
- [x] **Step 4 - wire into startup and download flow** - call `init_db()` on
  FastAPI startup in `backend/main.py`; call `upsert_video()` in
  `_run_download()` (`backend/routes/videos.py`) right after `write_meta()`
  succeeds. *Done when:* starting the app creates `data/index.db` if it's
  missing, and `test_start_download_and_status_success` (extended) shows the
  index row for the downloaded video matches its `meta.json` after the
  download completes.

## Files / areas

- `backend/db.py` - new: schema, `init_db`, `get_connection`, `upsert_video`,
  `rebuild_index`.
- `backend/test_db.py` - new: tests for the above, following the
  `isolated_data_root`/`tmp_path` monkeypatch pattern in `backend/test_storage.py`.
- `backend/main.py` - add a startup hook calling `db.init_db()`.
- `backend/routes/videos.py` - call `db.upsert_video()` in `_run_download()`.
- `backend/routes/test_videos.py` - extend the existing download success test
  to assert the index row.

## Data / contracts

`videos` table (SQLite, `data/index.db`), matching `project-overview.md` exactly - **load-bearing for Phase 6**:

| Column | Type | Notes |
|---|---|---|
| `video_id` | TEXT PRIMARY KEY | matches the video's folder name |
| `title` | TEXT | |
| `channel` | TEXT | |
| `duration_seconds` | INTEGER | |
| `date_added` | TEXT | ISO 8601 |
| `path` | TEXT | folder path for the video |

Derived/rebuildable only - never store a field here that isn't also in the
video's own `meta.json`, per `coding-standards.md`.

## Testing

`pytest` is configured (`AGENTS.md` Commands), so this is a test-gated
feature - every step above is pure logic (SQLite reads/writes, file
scanning) and ships a passing test in the same step:

- Step 1: schema creation via `init_db()`.
- Step 2: `upsert_video()` insert + update-in-place.
- Step 3: `rebuild_index()` against fixture `meta.json` files, including a
  stale-row-removed case.
- Step 4: extend `test_start_download_and_status_success` (integration,
  `TestClient`) to assert the index row after a download; add a startup test
  if one doesn't already cover `init_db()` being called.

## Notes for the AI

- No ORM - stdlib `sqlite3` only, per `coding-standards.md`.
- No migration framework - inline `CREATE TABLE IF NOT EXISTS`.
- Follow `backend/storage.py`'s pattern of module-level path constants
  (`DB_PATH`) so tests can `monkeypatch.setattr` them, matching
  `isolated_data_root` in the existing test files.
- Single local user, no auth/scoping concerns.
- Close connections explicitly (`try`/`finally` or context manager) - no
  connection pool needed at this scale.

## Notes from build (Autopilot)

Built via `/autopilot` in one pass, 4 checkpoint commits (one per step). One
self-review fix landed during Step 4: Python default-argument values are
bound once at function-definition time, so the original `db_path: Path =
DB_PATH` defaults on `get_connection`, `init_db`, `upsert_video`, and
`rebuild_index`'s `data_root` silently ignored any later `monkeypatch.setattr`
of the module constant. Switched all four to `param: Path | None = None`
resolved inside the function body. Caught by the extended
`test_start_download_and_status_success` test, which failed before the fix.

No P0/P1 audit findings. Verified with `pytest backend/` (28 passed) and a
manual app boot confirming `data/index.db` is created with the correct schema.
