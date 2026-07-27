# Feature: Handle very short clips / silence (transcription edge cases)

**From build-plan:** Phase 7: Polish & Edge Cases (item 2)
**Status:** complete

## Goal

Two related edge cases produce confusing results today, found by reading
`backend/routes/videos.py`, the transcription adapters, and `frontend/js/app.js`:

1. **Very short trim ranges.** `trim_video_audio` (`backend/routes/videos.py:159-179`)
   only validates `start_seconds >= 0`, `start_seconds < end_seconds`, and
   `end_seconds <= duration_seconds`. A sub-second range (e.g. 0.1s) passes
   validation, `ffmpeg` happily produces a near-empty clip, and the user is
   left with unusable audio and no explanation.
2. **Silent/empty transcripts.** Both transcription adapters
   (`backend/adapters/transcription/local_mlx.py`,
   `backend/adapters/transcription/openai_api.py`) can return a successful
   result with `text: ""` for a silent or near-silent clip - this is not an
   error, so the status ends as `"done"`. The frontend renders this as a
   blank transcript box with no messaging (`app.js:284-296` for the
   transcribe view, `app.js:507-515` for the library view), which looks
   broken rather than "nothing was said here."

## In scope

- Backend: reject trim ranges shorter than a minimum duration with a clear
  400 error, before `ffmpeg` ever runs.
- Frontend: when a fetched transcript's text is empty (after trimming
  whitespace), show a clear "no speech detected" message instead of a blank
  box, in both the transcribe view and the library view.
- Frontend: don't reveal the summarize controls in the transcribe view for
  an empty transcript (nothing meaningful to summarize, avoids a wasted AI
  call).

## Out of scope

- Changing the transcription adapters themselves - they already return
  legitimate results for silent audio; no error to catch there.
- The library view's "generate new summary format" controls - the library
  view doesn't currently gate the summarize UI on transcript content at
  all (pre-existing pattern), and adding that gate is a separate decision
  not required by this build-plan item.
- Any changes to the download or metadata-fetch paths.
- The pre-existing duplication findings F-03/F-04/F-05 in
  `blueprint/context/findings.md` - unrelated to this change's files.

## Build steps

- [x] **Step 1 - Minimum trim duration validation** - add
  `MIN_TRIM_DURATION_SECONDS = 1.0` next to `DURATION_WARNING_THRESHOLD_SECONDS`
  in `backend/routes/videos.py`. In `trim_video_audio`, raise
  `HTTPException(400, "Trim range must be at least 1 second.")` when
  `end_seconds - start_seconds < MIN_TRIM_DURATION_SECONDS`, checked
  alongside the existing range validation and before the `ffmpeg` call. Add
  `test_trim_too_short_returns_400` to `backend/routes/test_videos.py`
  following the existing `test_trim_invalid_range_returns_400` pattern.
  *Done when:* `pytest backend/routes/test_videos.py` passes including the
  new test, and a manual POST to `/api/videos/{id}/trim` with a 0.3s range
  returns 400 with the new message.

- [x] **Step 2 - Graceful empty-transcript display** - in
  `showTranscript` (`app.js:284-296`), when `body.text.trim() === ""`, set
  `transcriptDisplayEl.textContent` to `"No speech detected in this clip."`
  instead of the raw (empty) text, and leave `summarizeSection` hidden
  instead of revealing it. In the library detail loader
  (`app.js:507-515`), apply the same empty-text check so
  `libraryTranscriptDisplayEl` shows the same message instead of an empty
  string (the existing `"No transcript yet for this video."` branch for a
  failed fetch stays as-is). *Done when:* verified in a running browser -
  the library view against a seeded video folder with an empty
  `transcript.json` shows the message, and the transcribe view (via a
  Playwright-intercepted `/transcription/status` + `/transcript` response)
  shows the message with the summarize section still hidden.

## Files / areas

- `backend/routes/videos.py`
- `backend/routes/test_videos.py`
- `frontend/js/app.js`

## Data / contracts

None new. No response model changes - both fixes work off existing fields
(`TrimRequest.start_seconds`/`end_seconds`, `Transcript.text`).

## Testing

Test command: `pytest` (declared in `AGENTS.md`, test gate applies).

- Step 1 adds in-scope backend logic (a validation branch) - ships a unit
  test in the same diff, per `coding-standards.md`.
- Step 2 is frontend UI/display logic with no JS test runner configured -
  verified with browser evidence (Playwright) per the UI/integration
  exemption in `coding-standards.md`, not a unit test.

## Notes for the AI

- Keep the existing `HTTPException(400, ...)` pattern for the trim
  validation - don't introduce a new error shape.
- Don't touch the transcription adapters or the background-task status
  dicts (`_transcription_status`) - the "done" status for an empty
  transcript is already correct; this is a display-layer fix only.
- Reuse the existing `"No transcript yet for this video."` string style
  in the library view; don't rename or restructure existing DOM elements.

## Notes

Built via `/autopilot`. Spec was written fresh (no build-plan item existed
for this yet as an active spec) after a code survey of the trim endpoint,
both transcription adapters, and the frontend transcript-rendering paths;
self-critique before build found the scope already tight and made no
changes.

Step 1 verified with `pytest` (unit test) plus a manual API check. Step 2
verified with real browser evidence: a seeded video folder with an empty
`transcript.json` for the library view, and Playwright route interception
of `/transcription/status` + `/transcript` (driving the real
`pollTranscriptionStatus` -> `showTranscript` code path) for the transcribe
view - both confirmed via screenshot and DOM assertions
(`transcript-display` text, `summarize-section` hidden state). Seeded test
data and the background dev server were cleaned up afterward.

Targeted audit (scope: current, diff vs `main`) found no new P0-P3 issues.
Pre-existing open findings `F-03`/`F-04`/`F-05` in
`blueprint/context/findings.md` are unrelated to this change (background-task
status pattern, `video_id` path validation, and frontend error/poll
duplication elsewhere in `app.js`) and remain in the ledger, untouched.

## Findings

None raised or resolved by this feature.
