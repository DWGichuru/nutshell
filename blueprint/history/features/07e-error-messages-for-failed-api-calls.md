# Feature: Error messages for failed API calls

**From build-plan:** feature 7 (Polish & Edge Cases)
**Status:** complete

## Goal

Every action already has an inline error banner (`download-error`, `trim-error`,
`transcribe-error`, `summarize-error`, `library-error`, `library-summarize-error`),
but two real gaps let failures reach the user as nothing at all, or as a raw
SDK exception dump: status-polling silently hangs forever on a network hiccup,
and an invalid (not just missing) provider API key surfaces as a verbose raw
exception string instead of a clear message.

## In scope

- Catch `anthropic.AuthenticationError` in `backend/adapters/summarization/anthropic_api.py`
  and `openai.AuthenticationError` in `backend/adapters/summarization/openai_api.py` and
  `backend/adapters/transcription/openai_api.py`, before the existing generic
  `except Exception`, and raise the existing `SummarizationError`/`TranscriptionError`
  with a clean "Invalid `<Provider>` API key. Check your .env file." message instead
  of the raw SDK exception text.
- Stop the four recursive status-poll functions in `frontend/js/app.js`
  (`pollDownloadStatus`, `pollTranscriptionStatus`, `pollSummarizationStatus`,
  `pollLibrarySummarizationStatus`) from failing silently when a status request
  errors or the network drops: catch the failure and route it into each
  function's own existing "error" branch (stop the spinner, show the section's
  existing inline error message, clear the status text, re-enable the button)
  instead of leaving an unhandled rejection and a spinner that never stops.

## Out of scope

- No new toast/notification component - the existing per-section inline error
  banners already cover every action; this feature only makes sure every
  failure path actually reaches one of them.
- No change to `local_mlx.py` or local transcription error handling - no API
  key is involved there.
- No retry/backoff logic for polling - a single failure surfaces immediately,
  matching how every other failure in the app is already handled today.
- No change to the generic non-auth failure path in the adapters (network
  errors, rate limits, etc.) - those still fall through to today's existing
  generic `except Exception` wrapping, unchanged.

## Build steps

- [x] **Step 1 - Friendly invalid-API-key messages (backend)**
- [x] **Step 2 - Stop silent poll failures (frontend)**

## Files / areas

- `backend/adapters/summarization/anthropic_api.py` (+ `test_anthropic_api.py`)
- `backend/adapters/summarization/openai_api.py` (+ `test_openai_api.py`)
- `backend/adapters/transcription/openai_api.py` (+ `test_openai_api.py`)
- `frontend/js/app.js`

## Data / contracts

None - no new API shapes. The `{"status": "error", "error": str(exc)}` status
dict already returned by every `/api/videos/{video_id}/*/status` endpoint is
unchanged; only the message text carried inside it gets cleaner for auth
failures.

## Testing

- Step 1 added in-scope logic (choosing a friendlier message for a specific
  caught exception type), so it shipped a passing test per adapter in the
  same diff, per the testing gate in `coding-standards.md`.
- Step 2 was DOM/event-wiring only (no new pure logic function), so it rode
  on manual/browser verification rather than a new JS unit test - no JS test
  runner is configured in this project.

## Completion evidence

- `pytest`: 89 passed (86 pre-existing + 3 new tests for the friendly
  auth-error messages).
- Playwright: stubbed each of the four status endpoints (`/status`,
  `/transcription/status`, `/summarization/status` on both New Summary and
  Library) to fail, and confirmed for each that the section's existing error
  banner appears with the expected message, its spinner stops, and its button
  re-enables, instead of hanging indefinitely.
- Screenshots confirmed the error banner renders correctly in both light and
  dark mode.

The pre-existing P2/P3 ledger entries (duplicate status-tracking pattern,
unvalidated `video_id` path segments, duplicate frontend error/poll helpers,
placeholder truncation at 420px) remain open in `blueprint/context/findings.md`
for future work; none are P0/P1 and none block this completion.
