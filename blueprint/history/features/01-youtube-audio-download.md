# Feature: YouTube audio download

**From build-plan:** Phase 1: YouTube Download
**Status:** complete

## Goal

Let the user paste a YouTube URL, see its title/channel/duration (with a
warning if it's long), and download its best audio track into a per-video
folder on disk with a `meta.json` record. This is the entry point for every
later feature (trimming, transcription, summarization, library).

## In scope

- `POST /api/videos/metadata` - fetch title/channel/duration via `yt-dlp`
  without downloading; flag videos over a 60-minute threshold with an
  estimated transcription time.
- `derive_video_id`, folder creation, and `meta.json` read/write helpers in
  `backend/storage.py`.
- `POST /api/videos/download` - kick off the actual audio download (best
  track via `yt-dlp`, converted to `audio.mp3` via `ffmpeg` if needed) as a
  background task, plus `GET /api/videos/{video_id}/status` to poll progress.
- Basic error handling: invalid/unreachable URLs and download failures
  surface as a proper `HTTPException` / status field, never a raw 500 or
  crash.

## Out of scope

- SQLite index (`data/index.db`) - Phase 2.
- Any frontend UI (URL input, warning banner, progress indicator) - the
  frontend is introduced in Phase 3 alongside waveform trimming; this
  feature only builds the backend contract it will call.
- Waveform trimming, transcription, summarization - later phases.
- Persisting download status anywhere durable (DB, file) - status lives in
  an in-process dict, acceptable for a single-user local server that isn't
  expected to restart mid-download.

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight
   on. Checkpoints are optional; `/complete` makes the real feature-level
   commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the
step was too big, so split it.

## Build steps

- [x] **Step 1 - Metadata endpoint** - Add `backend/models.py` with
  `MetadataRequest` (`url: str`) and `VideoMetadataResponse`
  (`title`, `channel`, `duration_seconds`, `needs_confirmation: bool`,
  `estimated_minutes: float | None`). Add `backend/youtube.py` with a
  `fetch_metadata(url) -> dict` wrapper around `yt_dlp.YoutubeDL(...).extract_info(url, download=False)`,
  raising a clear exception on failure. Add `backend/routes/videos.py` with
  `POST /api/videos/metadata`, computing `needs_confirmation` /
  `estimated_minutes` via a small pure function (`duration_seconds > 3600`,
  estimate = `duration_seconds * 0.5`, i.e. a rough 2x-realtime local-Whisper
  guess) so it's unit-testable without calling `yt-dlp`. Wire the router into
  `backend/main.py`. *Done when:* posting a real short YouTube URL returns
  200 with correct title/channel/duration; a duration over 3600s returns
  `needs_confirmation: true` with an `estimated_minutes` value; an
  invalid/unreachable URL returns `HTTPException(400)`, not a 500.

- [x] **Step 2 - Storage helpers** - Add `VideoMeta` model to
  `backend/models.py` matching the `meta.json` schema in
  `project-overview.md` (`video_id`, `title`, `channel`,
  `duration_seconds`, `date_added`, `source_url`). Add `backend/storage.py`
  with `derive_video_id(info: dict) -> str` (yt-dlp's own video id,
  lowercased), `video_dir(video_id) -> Path` (`data/videos/{video_id}/`,
  created if missing), and `write_meta(video_id, meta: VideoMeta) -> None`
  / `read_meta(video_id) -> VideoMeta`. *Done when:* calling
  `write_meta`/`read_meta` round-trips all five fields correctly and
  produces a real `meta.json` file with those exact keys.

- [x] **Step 3 - Download endpoint** - Add `download_audio(url, dest_dir) -> Path`
  to `backend/youtube.py` (best-audio download via `yt-dlp`) and
  `convert_to_mp3(src_path) -> Path` (shells out to `ffmpeg` only if the
  downloaded file isn't already `.mp3`, then removes the intermediate file).
  Add `POST /api/videos/download` to `backend/routes/videos.py`: derives
  `video_id`, kicks off download + convert + `write_meta` as a
  `BackgroundTasks` job, returns `{video_id, status: "pending"}` immediately.
  Track per-`video_id` status (`"downloading" | "done" | "error"`, plus an
  error message) in an in-process dict. Add
  `GET /api/videos/{video_id}/status` returning that status, 404 if unknown.
  *Done when:* posting a real short YouTube URL eventually produces
  `data/videos/{video_id}/audio.mp3` + `meta.json`, and polling `/status`
  shows `pending`/`downloading` -> `done`; a download failure (mocked)
  surfaces `status: "error"` with a message instead of crashing the server.

## Files / areas

- `backend/models.py` (new) - Pydantic request/response models + `VideoMeta`.
- `backend/youtube.py` (new) - `yt-dlp` metadata fetch, audio download,
  `ffmpeg` conversion.
- `backend/storage.py` (new) - video id derivation, folder + `meta.json`
  helpers.
- `backend/routes/videos.py` (new) - the three endpoints above.
- `backend/main.py` - include the new `videos` router.
- Matching `test_*.py` files next to each new module.

## Data / contracts

- `meta.json` (per `project-overview.md`): `video_id`, `title`, `channel`,
  `duration_seconds`, `date_added` (ISO 8601), `source_url`. Load-bearing for
  Phase 2 (SQLite index scans this file) and Phase 6 (library view reads it)
  - don't drift from these field names.
- `video_id`: the YouTube video id itself (from `yt-dlp` info), lowercased -
  not a hash or slug. Phase 2's index and every later per-video route key off
  this same value.
- Download status shape (`{status, error}`) is in-process only, not part of
  the stored data model - fine to change later without a migration.

## Testing

`pytest` is configured and declared in `AGENTS.md`, so the test gate is on:
every step above ships a passing test in the same diff.

- Step 1: unit test the pure `needs_confirmation`/`estimated_minutes`
  function directly (edge cases: exactly 3600s, 0s, very long). Unit test
  the endpoint with `yt_dlp.YoutubeDL.extract_info` monkeypatched to a
  canned info dict (success path) and to raise (failure -> `HTTPException(400)`).
- Step 2: unit test `derive_video_id` against a fake info dict; unit test
  `write_meta`/`read_meta` round-trip using `pytest`'s `tmp_path` fixture
  (patch the data root so no real `data/videos/` files are touched).
- Step 3: unit test the download endpoint with `download_audio` and
  `convert_to_mp3` monkeypatched (success path writes `meta.json` correctly;
  failure path sets status `"error"`); unit test `GET /status` for an
  unknown `video_id` returning 404.
- Manual/integration proof beyond mocks: run the dev server and `curl` a
  real short YouTube URL end-to-end, confirm `data/videos/{id}/audio.mp3`
  and `meta.json` land on disk with correct fields - this is the build
  plan's own "Test: download a short video..." line, and mocks alone can't
  prove real `yt-dlp`/`ffmpeg` integration.

## Notes for the AI

- Long-running download work must not block the request thread - background
  task + polled status, per `coding-standards.md`. Keep the in-process
  status dict simple; don't add persistence or a job queue - out of scope
  for a single-user local tool.
- Never trust a client-supplied file path; every route takes a `video_id` or
  `url`, never a raw path, and resolves storage through
  `data/videos/{video_id}/`.
- Use `pathlib.Path` for all filesystem paths, type hints on every function
  signature, and Pydantic models (not raw dicts) at the API boundary, per
  `coding-standards.md`.
- The 0.5x-duration transcription estimate (Step 1) is a rough placeholder
  for the UI warning banner copy - flag it as an assumption when presenting
  this spec; adjust if you'd rather use a different multiplier.
- No `backend/adapters/` module here - that's reserved for the
  pluggable transcription/summarization providers in later phases. `yt-dlp`
  has one implementation, so it's a plain `backend/youtube.py` module.

## Findings

### 01-youtube-audio-download/F-01 [P1] closed - Download background task only caught YouTubeError

**File:** backend/routes/videos.py:66
**Found:** 2026-07-27 by /autopilot (scope: current, feature/youtube-audio-download)
**Why it matters:** `_run_download` only caught `YouTubeError`, so a non-yt-dlp
failure (a disk error from `write_meta`/`video_dir`, or any other unexpected
exception from `convert_to_mp3`) would leave `_download_status[video_id]`
stuck at `"downloading"` forever, with no path to `"error"`. Since status is
in-process only, that video would be unrecoverable without a server restart -
directly violating the feature's own done-when that a download failure
"surfaces `status: 'error'` ... instead of crashing the server."
**Suggested fix:** Broaden the except clause in `_run_download` to `except
Exception` so any failure in the background job resolves to an `"error"`
status (`YouTubeError` is already a subclass of `Exception`, so the narrower
branch was redundant once broadened).
**Resolution:** Fixed by widening `except YouTubeError` to `except Exception`
in `_run_download` (backend/routes/videos.py:66), and added
`test_start_download_unexpected_failure_sets_error_status` (backend/routes/test_videos.py)
covering a non-`YouTubeError` exception (`OSError`) from the background job.
Full suite (21 tests) reruns green after the fix; re-examined the repaired
code and confirmed the original gap is closed with no new defect introduced.
