# Feature: Transcription - local path (4b)

**From build-plan:** feature 4b (split from Phase 4: Transcription (Local + API))
**Status:** complete

## Goal

Add the on-device `mlx-whisper` transcription path alongside the existing
OpenAI API path from 4a, and let the user actually choose between them in the
UI. This closes out Phase 4: both transcription methods work end to end
through the same adapter interface, and a test confirms they produce
consistent output shapes with the correct method recorded.

## Split note

Continues the split from 4a's spec: 4a shipped the API-only path with the
shared adapter interface and a UI method picker that disabled "Local". 4b adds
the local adapter and turns that picker option on.

4a's spec flagged `mlx-whisper`'s Python 3.14 compatibility as unconfirmed.
Verified during this spec's prep: `pip install mlx-whisper` succeeds cleanly in
the project's Python 3.14 venv (native deps `mlx`/`mlx-metal`/`torch`/`numba`
all ship `cp314` wheels for macOS arm64). No blocker.

## In scope

- `mlx-whisper` local adapter implementing the existing
  `TranscriptionAdapter` interface (`transcribe(audio_path: Path) ->
  TranscriptResult`, `method="local"`).
- Endpoint dispatch: `POST /{video_id}/transcribe` runs the local adapter when
  `method="local"` instead of rejecting it with a 400.
- Enable "Local" in the frontend method picker (remove `disabled`, drop the
  "coming soon" copy); keep the API cost note as-is.
- A test that runs both adapters (mocked) against representative fixture data
  and asserts both produce the same `TranscriptResult` shape with the correct
  `method` field (`"local"` vs `"api"`) - the build-plan's "compare both
  methods" test, done via mocks rather than a real audio clip since neither
  adapter is exercised against live services in tests.

## Out of scope

- Real end-to-end accuracy comparison against a live audio clip (the build
  plan's "compare accuracy/timestamp alignment" is a manual `/try` check, not
  an automated test - accuracy isn't a deterministic assertion).
- Choosing or bundling a specific Whisper model size beyond a documented
  default; no UI for model selection.
- Any change to the API adapter or the status/transcript endpoints beyond the
  dispatch-by-method change in scope above.
- Progress percentage or granular local-processing progress (the existing
  pending/transcribing/done/error status is method-agnostic and already
  method-aware per 4a; a finer local progress bar is a future enhancement, not
  required by the build-plan line).

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight on.
   Checkpoints are optional; `/complete` makes the real feature-level commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the step was too big, so split it.

## Build steps

- [x] **Step 1 - Local mlx-whisper adapter** - Add `mlx-whisper` to
  `requirements.txt`. Implement `backend/adapters/transcription/local_mlx.py`
  with `transcribe(audio_path: Path) -> TranscriptResult` calling
  `mlx_whisper.transcribe(str(audio_path), path_or_hf_repo=MODEL)` (module
  constant `MODEL = "mlx-community/whisper-base-mlx"`), mapping the returned
  dict's `text` and `segments` (`start`/`end`/`text`) into `TranscriptResult`
  with `method="local"`; wrap failures in `TranscriptionError`. *Done when:* a
  unit test in `backend/adapters/transcription/test_local_mlx.py` mocks
  `mlx_whisper.transcribe` and confirms correct mapping, plus confirms an
  exception from `mlx_whisper.transcribe` raises `TranscriptionError`.
- [x] **Step 2 - Dispatch by method + cross-adapter consistency test** - In
  `backend/routes/videos.py`, replace the `method="local"` 400 rejection with
  dispatch to the local adapter (a small `method -> adapter callable` mapping
  next to the existing `transcribe_api` import), threading `request.method`
  through to `_run_transcription`. Add a test in
  `backend/adapters/transcription/test_consistency.py` that mocks both
  adapters' underlying clients (OpenAI + `mlx_whisper.transcribe`) with
  equivalent fixture data and asserts both return a `TranscriptResult` with
  matching `text`/`segments` shape and their respective correct `method`
  value. Add an endpoint test in `backend/routes/test_videos.py` mirroring the
  existing `method="api"` success test, but for `method="local"` (mocked
  adapter), confirming status reaches `done` and `transcript.json` is written
  with `method: "local"`. *Done when:* those tests pass and the existing
  `method="local"` 400 test is replaced/updated to reflect the new success
  path.
- [x] **Step 3 - Enable Local in the method picker** - In
  `frontend/index.html`, remove `disabled` from the Local radio input and
  replace the "coming soon" copy with a short note (on-device, free, first run
  downloads the model). In `frontend/js/app.js`, no logic change is expected
  since `startTranscription()` already reads the checked radio's value - this
  step is markup/copy only unless the browser check finds otherwise. *Done
  when:* browser check - both API and Local are selectable in the method
  picker, and selecting Local and clicking Transcribe calls the endpoint with
  `{"method": "local"}`.

## Files / areas

- `backend/adapters/transcription/local_mlx.py` (new)
- `backend/adapters/transcription/test_local_mlx.py` (new)
- `backend/adapters/transcription/test_consistency.py` (new)
- `backend/routes/videos.py` (dispatch by method instead of rejecting local)
- `backend/routes/test_videos.py` (extend: local success path, replace the old
  local-400 test)
- `requirements.txt` (add `mlx-whisper`)
- `frontend/index.html` (enable Local radio, update copy)

## Data / contracts

- No changes to `transcript.json`'s shape or the transcription status
  vocabulary - both were locked in 4a and this feature only adds a second
  producer of the same `TranscriptResult`/`Transcript` contract.
- `MODEL = "mlx-community/whisper-base-mlx"` is a local constant, not a contract
  consumed elsewhere - safe to change later without touching other features.

## Testing

`pytest` is configured and declared in `AGENTS.md`, so the test gate applies:
every logic-bearing step above ships a passing test in the same diff.

- Step 1: adapter test mocking `mlx_whisper.transcribe` - response mapping and
  the failure-wraps-in-`TranscriptionError` path. No real model download or
  inference in tests.
- Step 2: a cross-adapter consistency test (mocked) plus an endpoint test for
  the local success path; the existing `test_transcribe_local_method_returns_400`
  test in `test_videos.py` gets replaced since local is no longer rejected.
- Step 3 is UI-only (markup/copy) - verified by browser check, not a unit test.

## Notes for the AI

- Reuse `TranscriptSegment`/`TranscriptResult`/`TranscriptionError` from
  `backend/adapters/transcription/base.py` - do not redefine shapes.
- `mlx_whisper.transcribe` downloads its model from Hugging Face on first use
  and caches it; that's expected local-adapter behavior, not something to work
  around, but worth a one-line mention in the UI copy so the first real run
  isn't a surprise.
- Keep the endpoint dispatch minimal - a small mapping/if-branch by
  `request.method`, not a new abstraction layer; there are only two adapters.
- No em dashes; use hyphens or rephrase, per `coding-standards.md`.

## Findings

### 04b-transcription-local-path/F-01 [P2] closed - Duplicated OpenAI test doubles across two test files

**File:** backend/adapters/transcription/test_consistency.py:1
**Found:** 2026-07-27 by /autopilot (scope: current, feature 4b)
**Why it matters:** `test_consistency.py` (added in this feature) redefined
`FakeSegment`, `FakeTranscription`, `FakeTranscriptions`, `FakeAudio`, and
`FakeOpenAI` verbatim from `backend/adapters/transcription/test_openai_api.py`.
Two copies of the same fake OpenAI client drift independently the next time
either adapter's response shape changes.
**Suggested fix:** Extract the fakes into a shared, non-test module
(`backend/adapters/transcription/fakes.py`) and import them from both test
files.
**Resolution:** Fixed in the same pass - added
`backend/adapters/transcription/fakes.py` and updated
`test_openai_api.py`/`test_consistency.py` to import from it instead of
redefining. Re-ran `pytest` (49 passed). Re-examined both test files: no
remaining duplicate class definitions. Closed.
