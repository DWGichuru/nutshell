# Feature: Transcription - API path (4a)

**From build-plan:** feature 4a (split from Phase 4: Transcription (Local + API))
**Status:** complete

## Goal

Turn a trimmed audio file into a saved transcript using the OpenAI Whisper API,
behind a shared adapter interface that the local (`mlx-whisper`) path will plug
into next. This is the first working transcription path end to end: pick a
method, transcribe, see progress, see the transcript, with the result saved to
`transcript.json`.

## Split note

Phase 4 in `build-plan.md` covered both the local and API transcription paths,
the UI method picker, the endpoint, storage, progress, and a comparison test in
one line - too much for one reviewable spec. It's split into:

- **4a (this spec)** - adapter interface, OpenAI API adapter, endpoint, storage,
  method-aware progress, and a method picker UI where API is the working option.
- **4b (next)** - `mlx-whisper` local adapter, enabling Local in the picker, and
  the both-methods comparison test.

`mlx-whisper` compatibility with the project's Python 3.14 venv is unconfirmed
(package exists on PyPI at 0.4.3, but wheel/version support for 3.14 hasn't been
checked) - isolating it to 4b keeps that risk from blocking a working API path.

## In scope

- Shared transcription types (`TranscriptSegment`, `TranscriptResult`) and an
  adapter interface that both the API and (later) local adapters implement.
- OpenAI Whisper API adapter (`whisper-1`, verbose JSON for segment timestamps),
  reading `OPENAI_API_KEY` from `.env` via `python-dotenv`.
- `transcript.json` read/write helpers in `backend/storage.py`, matching the
  data model in `project-overview.md` (`text`, `segments`, `method`).
- Endpoint to trigger transcription on a video's (trimmed) audio, background
  task + polled status (pending/transcribing/done/error), matching the existing
  download-status pattern in `routes/videos.py`.
- Endpoint to fetch the saved transcript once done.
- Frontend: a method picker (API enabled, Local visibly disabled with a "coming
  soon" note and no cost-note requirement since it's not selectable yet),
  Transcribe button, progress indicator, transcript display.
- Unit tests for the adapter (mocked OpenAI client) and the endpoints (mocked
  adapter), per the test gate in `coding-standards.md`.

## Out of scope

- `mlx-whisper` local adapter and enabling "Local" in the method picker (4b).
- The both-methods comparison test (4b).
- Per-method cost note copy for API (nice-to-have UI text, not load-bearing -
  add only if trivial while building the picker; don't block the step on it).
- Summarization (Phase 5) and library reload of transcripts (Phase 6) - the
  transcript GET endpoint here only serves the just-transcribed video for
  display, not a full library integration.

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight on.
   Checkpoints are optional; `/complete` makes the real feature-level commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the step was too big, so split it.

## Build steps

- [x] **Step 1 - Transcript types and storage** - Add `TranscriptSegment` and
  `TranscriptResult` (dataclasses) in `backend/adapters/transcription/base.py`
  defining the shared adapter contract (`transcribe(audio_path: Path) ->
  TranscriptResult`, `method: Literal["local", "api"]`). Add a `Transcript`
  Pydantic model in `backend/models.py` matching `transcript.json`'s shape
  (`text: str`, `segments: list[{start, end, text}]`, `method: str`). Add
  `transcript_path`, `write_transcript`, `read_transcript` helpers to
  `backend/storage.py`. *Done when:* a unit test in `backend/test_storage.py`
  writes a `Transcript` and reads it back with matching fields.
- [x] **Step 2 - OpenAI Whisper API adapter** - Add `openai` to
  `requirements.txt`. Implement
  `backend/adapters/transcription/openai_api.py` with a `transcribe(audio_path:
  Path) -> TranscriptResult` that calls the OpenAI audio transcription endpoint
  (`whisper-1`, verbose JSON) and maps the response into `TranscriptResult`
  (segments with `start`/`end`/`text`, `method="api"`). Load `OPENAI_API_KEY`
  via `python-dotenv` (call `load_dotenv()` once at app startup in
  `backend/main.py`); raise a `TranscriptionError` if the key is missing or the
  API call fails. *Done when:* a unit test in
  `backend/adapters/transcription/test_openai_api.py` mocks the OpenAI client
  and confirms correct text/segment/method mapping, and confirms a missing API
  key raises `TranscriptionError` before any network call.
- [x] **Step 3 - Transcription endpoint and status** - Add a
  `TranscribeRequest` (`method: Literal["local", "api"]`),
  `TranscriptionStartedResponse`, and `TranscriptionStatusResponse`
  (`status`, `error: str | None`) to `backend/models.py`. Add
  `POST /api/videos/{video_id}/transcribe` to `backend/routes/videos.py`:
  runs the API adapter as a background task (same pattern as
  `_run_download`/`start_download`), tracks status in an in-memory dict keyed
  by `video_id` (`pending` -> `transcribing` -> `done`/`error`), and writes
  `transcript.json` via `write_transcript` on success. `method="local"` returns
  a 400 with a clear "not yet supported" message. Add
  `GET /api/videos/{video_id}/transcription/status` and
  `GET /api/videos/{video_id}/transcript` (404 if not yet transcribed). *Done
  when:* API tests in `backend/routes/test_videos.py` (mocking the adapter)
  cover: `method="api"` transitions pending -> done and persists
  `transcript.json` with `method: "api"`; `method="local"` returns 400;
  unknown `video_id` returns 404 from all three endpoints.
- [x] **Step 4 - Frontend method picker, progress, and transcript display** -
  Extend `frontend/index.html` and `frontend/js/app.js`: after a trim
  completes, show a transcription section with a method picker (API selected
  and enabled; Local shown but disabled with a short "coming soon" label), a
  Transcribe button that calls the new endpoint, status polling reusing the
  existing download-status polling pattern, and a transcript text display once
  status is `done`. *Done when:* browser check - after trimming a downloaded
  video and clicking Transcribe, a progress status appears, then the
  transcript text renders; the Local option is visibly disabled and cannot be
  selected.

## Files / areas

- `backend/adapters/transcription/base.py` (new)
- `backend/adapters/transcription/openai_api.py` (new)
- `backend/adapters/transcription/test_openai_api.py` (new)
- `backend/models.py` (add `Transcript`, `TranscribeRequest`,
  `TranscriptionStartedResponse`, `TranscriptionStatusResponse`)
- `backend/storage.py` (add transcript read/write helpers)
- `backend/test_storage.py` (extend)
- `backend/routes/videos.py` (add transcribe/status/transcript routes)
- `backend/routes/test_videos.py` (extend)
- `backend/main.py` (add `load_dotenv()` at startup)
- `requirements.txt` (add `openai`)
- `frontend/index.html`, `frontend/js/app.js` (method picker, progress, transcript display)

## Data / contracts

- `transcript.json` (per `project-overview.md`): `{"text": str, "segments":
  [{"start": float, "end": float, "text": str}], "method": "local" | "api"}`.
  Locking this now since Phase 5 (summarization) reads it and Phase 6
  (library) reloads it.
- `TranscriptResult` (adapter return type, not persisted directly - mapped to
  the `Transcript` Pydantic model before saving): same shape as above.
- Transcription status values: `"pending"`, `"transcribing"`, `"done"`,
  `"error"` - mirrors the existing download status vocabulary
  (`"pending"`/`"downloading"`/`"done"`/`"error"`) in `routes/videos.py`.

## Testing

`pytest` is configured and declared in `AGENTS.md`, so the test gate applies:
every logic-bearing step above ships a passing test in the same diff.

- Step 1: storage round-trip test (write/read `Transcript`).
- Step 2: adapter test mocking the OpenAI client - response mapping and the
  missing-API-key error path. No real network calls in tests.
- Step 3: endpoint tests mocking the adapter - status transitions, the
  `method="local"` 400, and 404s for an unknown `video_id`.
- Step 4 is UI/integration - verified by browser check (progress indicator
  behavior, transcript rendering, disabled Local option), not a unit test.

## Notes for the AI

- Follow the existing background-task + polled-status pattern already used for
  download (`_download_status`, `start_download`, `get_download_status` in
  `backend/routes/videos.py`) rather than introducing a new concurrency
  approach.
- Resolve all video data through `video_id` -> `data/videos/{video_id}/`, per
  `coding-standards.md`; never trust a client-supplied path.
- Raise `HTTPException` with real status codes for expected failures (missing
  video, unsupported method, missing API key); let unexpected errors 500.
- Keep the adapter interface generic now (`method: Literal["local", "api"]`)
  even though only `"api"` is implemented, so 4b only has to add an
  implementation, not reshape the contract.
- No em dashes; use hyphens or rephrase, per `coding-standards.md`.

## Findings

### 04a-transcription-api-path/F-01 [P3] closed - Dead constructor args on the OpenAI test double

**File:** backend/adapters/transcription/test_openai_api.py:35
**Found:** 2026-07-27 by /autopilot (scope: current, feature 4a)
**Why it matters:** `FakeOpenAI.__init__` accepted an unused `error` parameter
and an unused `**kwargs`, and defined a `__call__` method never invoked by any
test - the failure-path test built its own ad hoc `BoomClient`/`BoomAudio`/
`BoomTranscriptions` classes instead, leaving `error` looking load-bearing when
it wasn't. Dead parameters on a test double invite a future test to rely on
behavior that doesn't exist.
**Suggested fix:** Trim `FakeOpenAI` to only what its one caller uses
(`response`), and let the failure test keep its own dedicated fakes.
**Resolution:** Fixed in the same pass - removed `error`, `**kwargs`, and
`__call__` from `FakeOpenAI` (backend/adapters/transcription/test_openai_api.py:35-37).
Re-ran `pytest` (46 passed) confirming no test relied on the removed members.
Re-examined the file: no other unused members remain. Closed.
