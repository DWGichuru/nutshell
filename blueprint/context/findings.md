# Findings

> **Generated file.** The findings ledger: review findings raised by `/audit`
> against the work in progress, each with a durable ID, severity (P0-P3), and
> status. `/implement` marks repaired findings `fixed`, a later `/audit` pass
> moves them to `closed`, and `/complete` refuses to merge while any P0 or P1
> finding is `open` or `fixed`, then archives resolved findings with the work
> and resets this file.

### F-03 [P2] open - Download, transcription, and summarization background tasks duplicate the same status-dict pattern

**File:** backend/routes/videos.py:50
**Found:** 2026-07-27 by /autopilot audit (scope: current)
**Why it matters:** `_download_status`/`_run_download`, `_transcription_status`/
`_run_transcription`, and `_summarization_status`/`_run_summarization` are
three near-identical copies of the same
pending -> running -> done/error in-memory status tracking pattern. This
feature's step added the third copy, following the existing (already
duplicated) convention rather than introducing new duplication on its own.
Three copies is past the usual "rule of three" threshold for extracting a
shared helper.
**Suggested fix:** Extract a small shared helper (e.g. a generic status-store
class or a `run_background_job(status_map, video_id, fn)` wrapper) used by all
three background tasks. Out of scope for this feature since it would also
touch the existing download and transcription code paths, not just the new
summarization code.
**Resolution:**

### F-04 [P2] open - `video_id` path segments are not validated against traversal before being joined into filesystem paths

**File:** backend/storage.py:16
**Found:** 2026-07-27 by /autopilot audit (scope: current)
**Why it matters:** `video_dir`, `audio_path`, `transcript_path`, and the new
`summaries_dir` all build paths as `DATA_ROOT / video_id / ...` without
validating `video_id`. A malicious `video_id` path segment (e.g. containing
`..`) could resolve outside `data/videos/`. This is a pre-existing,
project-wide pattern (present in `video_dir`/`audio_path`/`transcript_path`
before this feature) that `summaries_dir` extends rather than introduces.
Single-user local tool lowers real-world risk, but `coding-standards.md`
already calls out "never trust a client-supplied file path."
**Suggested fix:** Add a single `video_id` validation/sanitization helper in
`backend/storage.py` (e.g. reject any id containing `/`, `\`, or `..`) used by
every path-building function. Best done as one cross-cutting hardening pass
covering all existing endpoints, not scoped to this feature alone.
**Resolution:**

### F-05 [P2] open - Frontend has six near-identical error-setter/status-poller function pairs, one per section

**File:** frontend/js/app.js:44
**Found:** 2026-07-27 by /autopilot audit (scope: current)
**Why it matters:** `setError`/`setTrimError`/`setTranscribeError`/
`setSummarizeError` already existed as four copies of the same
show/hide-message pattern; this feature's library view added
`setLibraryError`/`setLibrarySummarizeError` as a fifth and sixth copy,
following the existing (already duplicated) convention rather than
introducing new duplication on its own. The same applies to
`pollDownloadStatus`/`pollTranscriptionStatus`/`pollSummarizationStatus`/
`pollLibrarySummarizationStatus` - four near-identical pending -> done/error
polling loops. Six-plus copies is well past the "rule of three" threshold.
**Suggested fix:** Extract a shared `setFieldError(el, message)` helper and a
generic `pollStatus(url, { onDone, onError, intervalMs })` helper, used by all
sections. Out of scope for this feature since fixing it well means touching
the pre-existing download/trim/transcribe/summarize code paths too, not just
the new library code.
**Resolution:**

### F-06 [P2] fixed - Drawer nav active state didn't override the inactive dark-mode classes

**File:** frontend/js/app.js:57
**Found:** 2026-07-27 by /autopilot audit (scope: current)
**Why it matters:** `nav-library`'s markup hard-codes `dark:bg-espresso/60
dark:text-cream` alongside the base inactive classes. `INACTIVE_NAV_CLASSES`
(what `showNewSummaryView`/`showLibraryView` add/remove) didn't include those
`dark:` classes, so clicking to make Library active in dark mode added
`bg-terracotta` without removing the two-class-specificity `dark:` rules,
which always win the cascade over a single-class `.bg-terracotta` selector.
The active drawer item stayed dark/blended instead of showing the terracotta
highlight. Pre-existing in the old top-nav (same classes), but the persistent
drawer built in this feature makes it far more visible.
**Suggested fix:** Add `dark:bg-espresso/60` and `dark:text-cream` to
`INACTIVE_NAV_CLASSES` so the classList add/remove pair always fully swaps
state in both light and dark mode.
**Resolution:** Widened `INACTIVE_NAV_CLASSES` in `frontend/js/app.js` to
include the two `dark:` classes; verified via Playwright screenshot that
toggling New Summary/Library in dark mode now shows the terracotta highlight
correctly on whichever item is active.

### F-07 [P3] open - YouTube URL input placeholder truncates at the new 420px interaction-pane width

**File:** frontend/index.html:56
**Found:** 2026-07-27 by /autopilot audit (scope: current)
**Why it matters:** The download form keeps its original side-by-side
input+button layout, unchanged per this feature's scope (only the container
was restructured, not section internals). At the new fixed 420px
interaction-pane width, the input's placeholder text ("https://www.youtube.com/watch?v=...")
is visually clipped. Purely cosmetic - the field is still fully usable, just
harder to read the full placeholder. The approved prototype
(`prototypes/new-summary.html`) actually uses a stacked full-width button
below the input rather than side-by-side, which would fix this, but changing
the download form's internal layout was explicitly out of scope for 9a.
**Suggested fix:** In a follow-up step (9b or a small `/fix`), stack the
Download button below the URL input (matching the prototype) instead of
beside it.
**Resolution:**

### F-08 [P2] open - Trimming the default full-duration region can fail with a confusing "end_seconds exceeds video duration" error

**File:** frontend-react/src/hooks/useWaveform.ts:37
**Found:** 2026-07-30 by /autopilot audit (scope: current)
**Why it matters:** The initial region spans `{start: 0, end: duration}` where
`duration` comes from wavesurfer's `decode` event as a float (e.g.
`19.005542`). `backend/routes/videos.py` validates `end_seconds` against
`meta.duration_seconds`, which is stored as an int (`19`). Clicking Trim
immediately after a video finishes downloading, without first adjusting the
region, can send `end_seconds` slightly past the stored integer duration and
get rejected with a real but confusing 400. Verified reproducible during this
feature's Step 2 acceptance check. This is not a regression from the React
port - `frontend/js/app.js`'s `renderWaveform`/`trimSelection` post
`activeRegion.end` the same way, so the old app has the identical latent bug;
11b ported the behavior faithfully per its "match `frontend/js/app.js` exactly"
scope rather than introducing a fix that would diverge from parity.
**Suggested fix:** Clamp the initial region's `end` (and/or the trim request's
`end_seconds`) to `Math.min(decodedDuration, knownDurationSeconds)`, or have
the backend accept a small epsilon of slack. Touches the shared trim
contract both apps rely on, so best done as its own small `/fix` rather than
inside this feature.
**Resolution:**
