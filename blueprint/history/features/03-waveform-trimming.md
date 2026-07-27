# Feature: Waveform Trimming

**From build-plan:** feature 3 (Phase 3: Waveform Trimming - Frontend)
**Status:** done

## Goal

Give the user a way to visually trim a downloaded video's audio before
transcription: a single-page frontend (Tailwind + wavesurfer.js) that can
download a video via the existing Phase 1 backend, render its waveform, let
the user drag start/end handles and preview the selection, then call a new
backend endpoint that produces the trimmed audio via `ffmpeg`.

## Design reference

No mockup to replicate. Use the palette and typography already locked in
`project-overview.md` (Design section) as Tailwind theme values. Not a
visual-fidelity feature, so no reference image is needed. The light/dark
default flipped mid-build (see Step 8) - the app is now light-mode-first,
dark mode as option.

## In scope

- Basic frontend page structure (`frontend/index.html`, `frontend/js/app.js`)
  with Tailwind CDN and the project's theme colors.
- A minimal URL-paste-and-download flow that drives the existing
  `/api/videos/metadata`, `/api/videos/download`, and `/api/videos/{id}/status`
  endpoints, just enough to get audio onto the page for trimming.
- A new `GET /api/videos/{video_id}/audio` endpoint serving the video's
  `audio.mp3`.
- wavesurfer.js waveform rendering for the downloaded audio.
- Draggable trim region (start/end handles) via the wavesurfer Regions plugin.
- Playback preview of just the selected region.
- A new `POST /api/videos/{video_id}/trim` endpoint that runs `ffmpeg` to
  produce a trimmed audio file and replaces `audio.mp3` in place (per the data
  model: "the downloaded, and once trimmed, replaced/derived audio file").
- Wiring the frontend "Trim" button to the new endpoint and reloading the
  waveform from the trimmed result.
- Full playback transport for the loaded track: play/pause toggle, skip
  back, skip forward (in addition to the existing region-only Preview).
- App-wide light-mode-first default (dark mode remains available via the
  existing `dark:` Tailwind classes, just no longer the default).

## Out of scope

- The full "Home / New Summary" UX (duration-warning banner, confirmation
  dialog for long videos) - deferred; this feature only needs enough of a
  download entry point to reach the trim view.
- Library view / browsing past videos (Phase 6).
- Transcription trigger (Phase 4) - trimming just produces the final
  `audio.mp3`; nothing downstream consumes it yet.
- Keeping the original untrimmed audio as a separate backup file - the data
  model specifies `audio.mp3` is replaced/derived, not preserved twice.

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight on.
   Checkpoints are optional; `/complete` makes the real feature-level commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the step was too big, so split it.

## Build steps

- [x] **Step 1 - Frontend scaffold + minimal download flow** - `frontend/index.html` with Tailwind CDN and the project's theme colors; `frontend/js/app.js` wiring a URL input + "Download" button to the existing metadata/download/status endpoints (polling status until `done` or `error`); `backend/main.py` serves `frontend/index.html` at `/` and mounts `frontend/` as static. *Done when:* running `uvicorn backend.main:app --reload`, opening `localhost:8000`, pasting a video URL, and clicking Download shows the status reach `done` and `audio.mp3` exists on disk for that video.
- [x] **Step 2 - Serve audio + render waveform** - add `GET /api/videos/{video_id}/audio` (404 if the video or file doesn't exist) returning the `audio.mp3` file; include wavesurfer.js via CDN in the frontend and, once download status is `done`, initialize it against that endpoint. *Done when:* the waveform visually renders in the browser after a successful download; a pytest test covers the audio endpoint's 200 (file exists) and 404 (unknown video) cases.
- [x] **Step 3 - Draggable trim region** - add the wavesurfer Regions plugin, create one region spanning the full track, made draggable/resizable; display the current start/end as formatted `mm:ss` labels that update live as the region changes. *Done when:* dragging either handle in the browser visibly resizes the region and updates the displayed start/end labels.
- [x] **Step 4 - Playback preview** - add a "Preview" button that plays only the selected region and stops automatically at the region's end. *Done when:* clicking Preview audibly plays just the selected range and playback stops at the end of the region without user action.
- [x] **Step 5 - Backend trim endpoint** - add `trim_audio(src_path, start_seconds, end_seconds) -> Path` to `backend/youtube.py` (ffmpeg `-ss`/`-to`, same error-wrapping pattern as `convert_to_mp3`); add `TrimRequest`/`TrimResponse` models; add `POST /api/videos/{video_id}/trim` that validates `0 <= start < end` and `end <= meta.duration_seconds` (400 on violation), runs the trim, and replaces `audio.mp3`. *Done when:* pytest covers a successful trim (ffmpeg invoked with the right args, file replaced) and an invalid-range 400; existing tests still pass.
- [x] **Step 6 - Wire the Trim button** - frontend "Trim" button posts the selected region's start/end (seconds) to the new endpoint, shows a loading/success state, and reloads the waveform from the (now trimmed) audio. *Done when:* the full manual flow works end to end - paste URL, download, waveform renders, drag region, preview plays the selection, click Trim, waveform reloads showing the shorter trimmed audio.
- [x] **Step 7 - Full playback transport** - add play/pause toggle, skip-back, and skip-forward controls next to the existing Preview/Trim buttons, using wavesurfer's `playPause()`/`skip()`/`play`/`pause` events to drive button state. *Done when:* Play/Pause toggles playback of the full loaded track and its icon/label reflects current state; skip-back/skip-forward jump playback position by a fixed interval (5s) without restarting the track.
- [x] **Step 8 - Light-mode-first default** - remove the hardcoded `dark` class from `<html>` in `frontend/index.html` so the page renders light by default, keeping the existing `dark:` Tailwind classes as the (currently unreachable) dark variant; sync `coding-standards.md` and `project-overview.md`'s "dark mode first" language to "light mode first, dark mode as option". *Done when:* loading the page with no manual override shows the light (cream/ivory) palette, not the near-black dark palette.

## Files / areas

- `frontend/index.html`, `frontend/js/app.js` (new)
- `backend/main.py` - serve frontend, mount static files
- `backend/routes/videos.py` - new audio-serve and trim routes
- `backend/youtube.py` - new `trim_audio` function
- `backend/models.py` - `TrimRequest`, `TrimResponse`
- `backend/routes/test_videos.py`, `backend/test_youtube.py` - new tests

## Data / contracts

- `GET /api/videos/{video_id}/audio` -> `audio.mp3` file response (404 if
  missing). Load-bearing: later phases (transcription) will also need to read
  this file directly from disk, not necessarily through this route, but the
  route itself is what the frontend depends on going forward.
- `POST /api/videos/{video_id}/trim` body `{start_seconds: float, end_seconds: float}` -> `{status: "trimmed", duration_seconds: float}`. Replaces
  `audio.mp3` in place - load-bearing for Phase 4 (transcription reads
  `audio.mp3` as the final, trimmed source).

## Testing

- Test command is configured (`pytest`), so it's a gate: Step 2's audio route
  and Step 5's `trim_audio` + trim endpoint (range validation, ffmpeg
  invocation, file replacement) are pure/branchy logic and ship tests in the
  same steps, following the existing `convert_to_mp3`/`test_videos.py` mocking
  patterns (monkeypatch `subprocess.run`, isolate `DATA_ROOT`/`DB_PATH` via
  `tmp_path`).
- Steps 1, 3, 4, 6 are UI/integration (wavesurfer rendering, drag handles,
  playback, end-to-end wiring) - verified by running the dev server and
  checking behavior in the browser, not unit tests.

## Notes for the AI

- Keep Step 1's download flow minimal: no duration-warning banner, no styling
  polish beyond the theme colors - just enough to reach the trim view.
- Never trust a client-supplied file path; resolve everything through
  `video_id` -> `data/videos/{video_id}/` as the rest of the backend already
  does.
- Match the existing error-handling pattern: `YouTubeError` from adapter code,
  translated to `HTTPException` at the route layer.
- wavesurfer.js and its Regions plugin load via CDN `<script>` tags, matching
  the "no build step" frontend convention already in `coding-standards.md`.
