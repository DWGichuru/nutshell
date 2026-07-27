# Feature: AI Summarization (Phase 5)

**From build-plan:** Phase 5: AI Summarization
**Status:** complete

## Goal

Turn a saved transcript into a saved AI summary. The user picks a format
(paragraph, bullet points, or chaptered/timestamped) after transcription
finishes, the backend calls a summarization provider, and the result is saved
to `summaries/{timestamp}_{format}.md` per `project-overview.md`'s data model.
Multiple summary runs per video are preserved, never overwritten, and a new
format can be generated from an already-transcribed video without
re-transcribing.

## In scope

- A summarization adapter interface (`backend/adapters/summarization/base.py`)
  mirroring the transcription adapter pattern: a `SummaryFormat` literal
  (`"paragraph" | "bullets" | "chaptered"`), a plain input shape carrying the
  transcript text and segments, and a `SummarizationError` for adapter
  failures.
- One working adapter (`backend/adapters/summarization/anthropic_api.py`)
  using the Anthropic Messages API, reading `ANTHROPIC_API_KEY` via
  `python-dotenv`. The chaptered format uses transcript segment timestamps;
  paragraph and bullets use the plain text.
- `backend/storage.py` helpers: `summaries_dir(video_id)`,
  `write_summary(video_id, format, content) -> Path` (filename
  `{timestamp}_{format}.md`, filesystem-safe timestamp), and
  `list_summaries(video_id)` returning saved summaries newest-first.
- Endpoint to trigger summarization on a video's saved transcript
  (`POST /api/videos/{video_id}/summarize`), background task + polled status
  (`pending -> summarizing -> done/error`), matching the existing
  download/transcription status pattern in `routes/videos.py`.
- Endpoint to list a video's saved summaries
  (`GET /api/videos/{video_id}/summaries`).
- Frontend: a format picker (paragraph/bullets/chaptered radios), a
  "Summarize" button that appears once a transcript exists, a progress
  indicator, and a rendered display of the generated summary. Selecting a new
  format re-triggers summarization without re-transcribing.
- A second summarization provider (`backend/adapters/summarization/openai_api.py`)
  using the OpenAI Chat Completions API, reading the existing `OPENAI_API_KEY`
  (already used for transcription, no new env var). Selected per run via a
  `provider` field on `SummarizeRequest` (`"anthropic" | "openai"`, default
  `anthropic`), with a matching provider picker in the UI next to the format
  picker - mirroring the transcription method picker.
- Unit tests for both adapters (mocked Anthropic and OpenAI clients) and the
  endpoints (mocked adapters), per the test gate in `coding-standards.md`.
- Add `anthropic` to `requirements.txt` (`openai` is already present from the
  transcription feature).

## Out of scope

- Summarization providers beyond Anthropic and OpenAI (Phase 8, optional).
- Library view integration - browsing past videos, reloading past summaries
  from the library, or a full history browser (Phase 6). This spec's list
  endpoint only serves the just-transcribed video's own summaries panel.
- Delete-video, export options, manual index resync (Phase 8).
- Editing or deleting a previously generated summary file.

## Build steps

- [x] **Step 1 - Summarization adapter interface and storage helpers** - Add
  `backend/adapters/summarization/base.py` with `SummaryFormat = Literal["paragraph",
  "bullets", "chaptered"]`, a `SummaryInput` dataclass (`text: str`, `segments:
  list[TranscriptSegment]` reusing the existing transcription segment shape),
  a `SummarizationAdapter` Protocol (`summarize(input: SummaryInput, format:
  SummaryFormat) -> str`), and `SummarizationError`. Add `summaries_dir`,
  `write_summary`, and `list_summaries` to `backend/storage.py`
  (`write_summary` creates `data/videos/{video_id}/summaries/` if needed and
  writes `{timestamp}_{format}.md` using a filesystem-safe timestamp format
  such as `%Y%m%dT%H%M%SZ`; `list_summaries` globs that folder and returns
  entries sorted newest-first with `format`, `created_at`, and `content`).
  *Done when:* a unit test in `backend/test_storage.py` writes two summaries
  for the same video (different formats) and confirms both are listed,
  newest-first, with correct content and no overwrite.

- [x] **Step 2 - Anthropic summarization adapter** - Add `anthropic` to
  `requirements.txt`. Implement `backend/adapters/summarization/anthropic_api.py`
  with a `summarize(input: SummaryInput, format: SummaryFormat) -> str` that
  reads `ANTHROPIC_API_KEY` via `python-dotenv`, raises `SummarizationError` if
  the key is missing (before any network call) or the API call fails, and
  builds a format-specific prompt: `paragraph` (a flowing prose summary),
  `bullets` (a bulleted key-points list), `chaptered` (timestamped sections
  using `input.segments`). Returns the model's markdown text. *Done when:* a
  unit test in `backend/adapters/summarization/test_anthropic_api.py` mocks
  the Anthropic client for all three formats, confirms the returned content,
  and confirms a missing API key raises `SummarizationError` before any
  network call.

- [x] **Step 3 - Summarization endpoint and status** - Add
  `SummarizeRequest` (`format: Literal["paragraph", "bullets", "chaptered"]`),
  `SummarizationStartedResponse`, `SummarizationStatusResponse` (`status`,
  `error: str | None`), and `SummaryEntry`/`SummaryListResponse`
  (`format`, `created_at`, `content`) to `backend/models.py`. Add
  `POST /api/videos/{video_id}/summarize` to `backend/routes/videos.py`: loads
  the saved transcript via `read_transcript`, 404s if missing, runs the
  adapter as a background task (same pattern as `_run_transcription`), tracks
  status in an in-memory dict keyed by `video_id`, and writes the result via
  `write_summary` on success. Add `GET /api/videos/{video_id}/summarization/status`
  and `GET /api/videos/{video_id}/summaries`. *Done when:* a test in
  `backend/routes/test_videos.py` starts summarization for a video with a
  saved transcript, polls status to `done`, and confirms the summary shows up
  in the list endpoint; a second test confirms `404` when no transcript
  exists yet, and a third confirms adapter failure surfaces as `status:
  "error"` with the message.

- [x] **Step 4 - Frontend format picker and summary display** - Add a
  "Summarize" section to `frontend/index.html` (format radios, Summarize
  button, status/error text, rendered summary output), shown once a
  transcript exists. Add the matching logic to `frontend/js/app.js`: trigger
  `POST /summarize` with the selected format, poll
  `/summarization/status`, then fetch and render `/summaries` (most recent
  entry) on completion. Selecting a different format and clicking Summarize
  again re-triggers without touching transcription. *Done when:* manually
  exercised in the browser - generate a `bullets` summary, confirm it renders,
  then generate `chaptered` for the same video and confirm both are visible
  behavior (new one displayed, prior one still present in
  `data/videos/{video_id}/summaries/` on disk).

- [x] **Step 5 - OpenAI summarization provider** - Extract the shared
  prompt-building logic (`FORMAT_INSTRUCTIONS`, `format_timestamp`,
  `build_prompt`) from `anthropic_api.py` into
  `backend/adapters/summarization/base.py` so both providers share identical
  format prompts. Implement `backend/adapters/summarization/openai_api.py`
  with a `summarize(input: SummaryInput, format: SummaryFormat) -> str` using
  the OpenAI Chat Completions API (`gpt-4o-mini`), reading `OPENAI_API_KEY`,
  raising `SummarizationError` on a missing key or API failure. Add
  `provider: Literal["anthropic", "openai"] = "anthropic"` to
  `SummarizeRequest`; `_run_summarization` in `routes/videos.py` picks the
  adapter by `provider`. Add a provider radio picker to the Summarize section
  in `frontend/index.html`/`app.js`, sent alongside `format`. *Done when:* a
  unit test mocks the OpenAI client for all three formats and confirms a
  missing key raises `SummarizationError` before any network call; a route
  test starts summarization with `provider: "openai"` and confirms the
  OpenAI-backed summary is saved and listed; existing anthropic-provider tests
  keep passing unchanged (default provider stays `anthropic`).

## Testing plan

Test command: `pytest` (declared in `AGENTS.md`). This project's test gate is
on, so each step above ships its own passing test alongside the logic it
adds - storage round-trip (step 1), adapter format/error handling (step 2),
endpoint status/list/error behavior (step 3), and OpenAI adapter/provider
selection (step 5). Step 4 is UI wiring and rides on browser verification, not
a new unit test.

## Findings

### 05/F-01 [P1] closed - Same-format summaries within the same second silently overwrite each other

**File:** backend/storage.py:62
**Found:** 2026-07-27 by /autopilot audit (scope: current)
**Why it matters:** `write_summary` names files `{timestamp}_{format}.md` with
second-level resolution (`%Y%m%dT%H%M%SZ`). Two summarization runs for the same
video and format within the same second collide on the same filename and the
second write silently overwrites the first, losing its content. This directly
violates `project-overview.md`'s data model: "Multiple summary runs per video
are all preserved, never overwritten." Reproduced by calling `write_summary`
twice in a row for the same video/format and confirming only one file exists
with the second call's content.
**Suggested fix:** Use a higher-resolution timestamp (microseconds) in the
filename so two calls in the same request cycle cannot collide.
**Resolution:** Fixed by switching `SUMMARY_TIMESTAMP_FORMAT` to
`%Y%m%dT%H%M%S%fZ` (microsecond resolution) in backend/storage.py. Re-ran the
reproduction script: two consecutive `write_summary` calls for the same
video/format now produce two distinct files, and `list_summaries` returns both
entries with their original content intact. Added
`test_write_summary_same_format_does_not_overwrite` to
backend/test_storage.py to lock in the fix. Full suite passes. Recheck: rebuilt
the original reproduction against the fixed code post-repair, confirmed the
collision no longer occurs and no new defect was introduced. Closed.

### 05/F-02 [P2] closed - `GET /summaries` returns 200 with a filesystem side effect for an unknown video_id instead of 404

**File:** backend/routes/videos.py:250
**Found:** 2026-07-27 by /autopilot audit (scope: current)
**Why it matters:** Every other video-scoped endpoint (`/status`, `/audio`,
`/transcript`, `/transcription/status`) 404s when `video_id` doesn't exist.
`get_summaries` instead calls `list_summaries`, which calls `summaries_dir`,
which unconditionally creates `data/videos/{video_id}/summaries/` even for a
video that was never downloaded, then returns `200 {"summaries": []}`. This is
inconsistent with the established pattern in this file and pollutes
`data/videos/` with empty folders for any video_id a client happens to query.
Reproduced by calling `list_summaries` for a nonexistent video_id and
confirming the directory is created on disk.
**Suggested fix:** Validate the video exists (via `read_meta`) before listing,
404 if not, matching the sibling endpoints; make `list_summaries` read-only
(don't create the directory just to list it).
**Resolution:** Fixed: `get_summaries` now calls `read_meta` first and raises
404 for an unknown `video_id`. `list_summaries` in backend/storage.py no
longer creates the summaries directory - it globs directly and returns an
empty list if the directory doesn't exist. Added
`test_get_summaries_unknown_video_id_returns_404` (replacing the old
empty-list test) to backend/routes/test_videos.py and
`test_list_summaries_missing_directory_returns_empty_list_without_creating_it`
to backend/test_storage.py. Full suite (64 tests) passes. Recheck: confirmed
`list_summaries` no longer creates a directory for an unknown video_id and no
new defect was introduced. Closed.
