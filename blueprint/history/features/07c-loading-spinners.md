# Feature: Loading states/spinners for download, transcription, and summarization

**From build-plan:** Phase 7: Polish & Edge Cases (item 3)
**Status:** complete

## Goal

The download, transcription, and summarization flows already show text-only
status during their background work (`pollDownloadStatus`,
`pollTranscriptionStatus`, `pollSummarizationStatus`, and the library view's
`pollLibrarySummarizationStatus`, which drives the same summarization step
from the Library tab). There is no visual indicator that work is in flight
beyond a text string next to a disabled button, which is easy to miss.

## In scope

- Add a small inline spinner next to the status text for all four in-flight
  flows (download, transcribe, summarize, library-summarize), visible while a
  request is starting or polling shows a `pending`/`running`-type status, and
  hidden once the flow reaches `done` or `error`.
- Frontend-only change; no backend or data model changes.

## Out of scope

- The synchronous trim step (no polling loop, already covered by
  button-disable).
- The broader status-pattern/error-setter duplication flagged in
  `blueprint/context/findings.md` (F-03, F-05) - pre-existing, cross-cutting
  refactors explicitly deferred by that ledger, not part of this polish item.

## Build steps

- [x] **Step 1 - Spinner markup and shared helper** - added a hidden
  `animate-spin` Tailwind element next to each of the four status elements
  (`download-status`, `transcribe-status`, `summarize-status`,
  `library-summarize-status`) in `frontend/index.html`, and one shared
  `setSpinner(el, isBusy)` helper in `frontend/js/app.js`, wired into all
  four flows' start functions (spinner on) and their `done`/`error` branches
  plus fetch-failure catch blocks (spinner off).
- [x] **Step 2 - Browser verification** - verified with Playwright, route
  mocking the download/transcribe/summarize/library-summarize endpoints to
  drive the real `startX`/`pollXStatus` code paths without hitting real
  yt-dlp/transcription/summarization services: spinner shows while in
  flight and hides on both `error` and `done` for all four flows, with no
  console errors. Confirmed dark-mode rendering via screenshot (spinner
  contrast against the dark surface).

## Files / areas

- `frontend/index.html`
- `frontend/js/app.js`

## Data / contracts

None. Purely a display-layer addition on top of existing status strings
already returned by `/status`, `/transcription/status`, and
`/summarization/status`.

## Testing

UI-only change (spinner visibility tied to existing status strings, no new
parsing/formatting/validation logic) - per `coding-standards.md`, verified
with browser evidence, not a new unit test. `pytest` (89 tests) re-run as a
sanity check and passed, unaffected by this frontend-only change.

## Notes for the AI

- Keep the spinner logic to one shared `setSpinner` helper; don't add a
  fifth/sixth bespoke spinner toggler alongside the existing per-section
  duplication already tracked in F-05.
- Don't touch the trim flow or backend status-tracking code - out of scope
  for this polish item.

## Notes

Built via `/autopilot`. Spec was written fresh (no build-plan item existed
for this yet as an active spec) after reading `frontend/js/app.js` and
`frontend/index.html` to confirm the exact status-polling shape for all four
flows.

Verified with Playwright route interception driving the real production
code paths (not manual DOM manipulation) for download, transcribe, and
summarize; the library-summarize flow was verified against a real seeded
library video with only the `/summarize` and `/summarization/status`
endpoints mocked. Dark-mode spinner contrast confirmed via screenshot. Dev
server and mock routes were cleaned up afterward.

Targeted self-review of the diff found no new P0-P3 issues: the change is
symmetric across the same four functions already covered by pre-existing
open findings `F-03`/`F-05` and does not deepen that duplication in any new
way. `F-04` (video_id path validation) is unrelated to this change. All
three remain `open` in `blueprint/context/findings.md`, untouched.

An unrelated, pre-existing uncommitted edit to `blueprint/build-plan.md`
(a stray duplicated Phase 8 checkbox line) was found on the branch before
this feature's own build-plan edit; confirmed with the user as accidental
and discarded before checking off this item.

## Findings

None raised or resolved by this feature.
