# Feature: Library View (Search/Filter)

**From build-plan:** Phase 6: Library View (Search/Filter)
**Status:** complete

## Goal

Browse past videos by title/channel/date, reload a video's stored transcript
and summaries, and generate a new summary format without re-downloading or
re-transcribing.

## In scope

- List endpoint over the SQLite index (`db.list_videos`), with optional
  title/channel substring search and `date_added` range filtering.
- Detail endpoint to fetch a single video's `meta.json` by `video_id`, for the
  "select video" reload flow (no existing endpoint returned bare `VideoMeta`).
- Frontend library view: a nav toggle between the existing "New Summary" flow
  and a new "Library" view, a search input, optional date-from/date-to
  inputs, a results list, and a "select video" detail panel that shows the
  transcript and past summaries, plus a format picker that calls the
  existing `/summarize` endpoint against the already-transcribed video.

## Out of scope

- Deleting a video, exporting a transcript/summary, or a manual index resync
  button - all explicitly Phase 8 (Optional/Future) in `build-plan.md`.
- Any change to the download/trim/transcribe flow itself.
- Rebuilding `index.db` as part of this feature; `rebuild_index` already
  exists from Phase 2.

## Build steps

- [x] **Step 1 - DB layer** - added `list_videos` to `backend/db.py` (search +
  date range filtering, `ORDER BY date_added DESC`, LIKE-wildcard escaping for
  the search term). *Done when:* `pytest backend/test_db.py` passes with 8 new
  tests covering no-filter, title match, channel match, case-insensitivity,
  date range, combined filters, and ordering.

- [x] **Step 2 - Backend routes** - added `VideoSummaryModel`/`VideoListResponse`
  to `backend/models.py`; added `GET /api/videos` (list/search) and
  `GET /api/videos/{video_id}` (single video meta, 404 on missing) to
  `backend/routes/videos.py`. *Done when:* `pytest backend/routes/test_videos.py`
  passes with 6 new tests (empty list, populated list, search filter, date
  filter, single video meta, unknown video_id 404).

- [x] **Step 3 - Frontend library view** - added a nav toggle between
  "New Summary" and "Library" views in `frontend/index.html`, with a search
  input, date-from/date-to inputs, a results list, and a detail panel
  (transcript + summaries + format/provider picker + summarize button) that
  reuses the existing `/summarize` endpoint scoped to the selected library
  video. Wired in `frontend/js/app.js`. *Done when:* browser verification
  passed (see Step 5 below).

- [x] **Step 4 - Verify (search across multiple videos)** - confirmed against
  5 real seeded videos across 2 channels: unfiltered list returns all, title
  substring search narrows correctly, channel substring search narrows
  correctly, a date range narrows correctly, and selecting a video reloads its
  transcript and summaries without hitting `/download`, `/trim`, or
  `/transcribe`.

- [x] **Step 5 - Acceptance check** - Playwright (system-installed, not added
  as a project dependency) verification against the running dev server and
  real data: nav toggle, search/date filtering, select-video reload, Enter-key
  search, rapid video-switching, and a network-intercepted summarize
  submission (avoided a real paid provider call) confirming the correct
  `POST /summarize` payload and status-poll wiring. Zero console/page errors.
  Two issues found during self-review and fixed in the same pass: a race
  condition where switching the selected video mid-load could let a stale
  response overwrite the newer selection (guarded with a
  `currentLibraryVideoId` check after every await), and a missing Enter-key
  handler on the search/date inputs (added).

## Testing plan

Test command: `pytest` (declared in `AGENTS.md`; no separate `Verify` command
configured, so the fallback test gate applies). Backend logic
(`list_videos` filtering, the two new routes) shipped unit tests per the test
gate - 14 new tests, 85 passing project-wide. Frontend nav toggle/rendering is
UI-only and was verified by browser/API evidence, not unit tests, per
`coding-standards.md`.

## Notes

A targeted audit (scope: this feature's diff) found no P0/P1 issues. It
logged one new P2 finding, `F-05` (frontend error-setter/status-poller
duplication extending an existing pre-feature pattern), which remains open in
`blueprint/context/findings.md` alongside the pre-existing `F-03` and `F-04` -
none block completion (P2/P3 only).
