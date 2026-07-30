# Feature: React frontend rewrite - New Summary flow

**From build-plan:** feature 11b
**Status:** complete

## Goal

Build the New Summary page's full pipeline in `frontend-react/` on top of 11a's
shell and shared components: paste a URL, preview its metadata before
downloading (closing gap #2 from Phase 11's goal), download, trim the
waveform, transcribe, and summarize - each stage revealed as the previous one
completes, matching `frontend/js/app.js`'s behavior exactly except where noted
below. The old `frontend/` app keeps serving `:8000` unchanged; this feature
only touches `frontend-react/`.

## In scope

- `usePolling` hook: one generic implementation replacing the old app's four
  duplicated recursive-`setTimeout` pollers, built against 11a's locked
  `nextPollAction` contract, with explicit cleanup (so it doesn't leak timers
  across unmounts/StrictMode's double-invoke) and a caught-fetch-failure path
  that routes into the caller's error handler instead of throwing unhandled -
  the same defect class the just-completed "error messages for failed API
  calls" feature fixed in the old app; this hook must not reintroduce it.
- `NewSummaryPage` container replacing `App.tsx`'s placeholder for the
  `"new-summary"` page: owns `videoId`, `isDownloaded`, `isTrimmed`,
  `transcript`, and `latestSummary` as plain `useState` (see Notes on why this
  is simpler than the reducer/pipeline-hook sketched during Phase 11
  planning), renders the real `DownloadSection`/`TrimSection`/
  `TranscribeSection`/`SummarizeSection` in the `ResizablePane`'s left content,
  and the real `AiPane` (or the existing empty-state placeholder, until a
  transcript exists) on the right.
- `DownloadSection`: URL input, a **Preview** step calling
  `POST /api/videos/metadata` (via `previewMetadata` from 11a's API client) to
  show title/channel/duration before committing to a download; if
  `needs_confirmation` is true, a warning banner with `estimated_minutes` and
  a **Confirm & Download** button; otherwise a direct **Download** button.
  Download calls `startDownload`, then `usePolling` against
  `getDownloadStatus` until `done`, revealing the Trim section.
- `useWaveform` hook + `TrimSection`: wavesurfer.js v7 + Regions plugin,
  ported faithfully from `renderWaveform`/`onVideoReady` (colors, region
  config, play/pause/skip/preview/trim wiring - see Data / contracts). Adds
  `wavesurfer.js` as an explicit new dependency.
- `TranscribeSection`: method radio (API checked by default, matching today),
  `startTranscription` + `usePolling` against `getTranscriptionStatus`, then
  `getTranscript`; the empty-transcript case shows "No speech detected in
  this clip." in the Transcript tab and hides the Summarize section entirely,
  exactly like `showTranscript` does today.
- `SummarizeSection`: provider radio (Anthropic checked by default),
  `startSummarization` + `usePolling` against `getSummarizationStatus`, then
  `getSummaries` (`summaries[0]` only - the single-latest-summary shape,
  distinct from 11c's full-history view).
- `AiPane`: wraps 11a's shared `Tabs` (Transcript/Summary), resetting to the
  Transcript tab whenever a new transcript loads, matching `activeAiTab`'s
  reset behavior today.
- All four sections use 11a's shared `AsyncStatus` for their busy/status/error
  display, so every failure path (invalid URL, a rejected trim range, a
  transcription/summarization failure - including the clean auth-error
  messages the backend now returns per the just-completed error-messages
  feature) surfaces to the user instead of failing silently, matching that
  feature's intent in the new app from day one.
- A real correctness improvement over today's app, made possible by
  consolidating video id into one piece of state (flagged as a goal in 11a):
  starting a second download in the same session resets `isTrimmed`/
  `transcript`/`latestSummary`, so stale trim/transcribe/summarize sections
  from a previous run don't linger. Today's vanilla app doesn't reset these on
  a fresh download - call this out during review as an intentional fix, not
  scope creep.

## Out of scope

- Library page - 11c.
- Dark mode toggle, wordmark/favicon - 11d.
- Backend serving cutover, deleting `frontend/` - 11e.
- Any change to `backend/` - every endpoint used here already exists and is
  unchanged.
- Local (`mlx-whisper`) transcription correctness itself - this feature wires
  the method picker and polling identically for both methods; it doesn't
  change how either adapter behaves.

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight on.
   Checkpoints are optional; `/complete` makes the real feature-level commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the step was too big, so split it.

## Build steps

- [x] **Step 1 - `usePolling` hook + metadata preview + download** - Write
      `src/hooks/usePolling.ts` (generic over 11a's `PollableStatus`/
      `nextPollAction`, restarts when its `key` changes, cleans up its timer
      on unmount/key-change, catches `fetchStatus` rejections and routes them
      through the same `onError` path as a `status: "error"` response). Write
      `src/pages/NewSummaryPage/NewSummaryPage.tsx` and
      `src/pages/NewSummaryPage/DownloadSection.tsx`; replace `App.tsx`'s
      `"new-summary"` placeholder branch with `<NewSummaryPage />`. *Done
      when:* against the real running backend, entering a real short YouTube
      URL and clicking Preview shows its title/channel/duration; a long video
      (or one forced over the threshold) shows the warning banner and
      requires Confirm & Download; clicking through downloads the video,
      status text updates via `usePolling`, and the Trim section is revealed
      on completion; an invalid URL shows the error via `AsyncStatus`.
- [x] **Step 2 - Waveform trim** - `npm install wavesurfer.js`. Write
      `src/hooks/useWaveform.ts` and
      `src/pages/NewSummaryPage/TrimSection.tsx`, ported from
      `renderWaveform`/`onVideoReady`/`togglePlayPause`/`skipBack`/
      `skipForward`/`previewSelection`/`trimSelection` (see Data / contracts
      for the exact config to preserve). *Done when:* for a downloaded video,
      the waveform renders, dragging the region updates the Start/End labels,
      Preview plays the selected range, Play/Pause and both skip buttons
      work, and Trim posts the range, reloads the waveform showing the
      trimmed duration, and reveals the Transcribe section - verified against
      the real backend, including trimming the same video 2-3 times in a row
      with no console errors (StrictMode double-effect / AudioContext leak
      check). Also drag the region to under a second and confirm the
      backend's real "Trim range must be at least 1 second." validation
      error surfaces via `AsyncStatus` instead of failing silently.
- [x] **Step 3 - Transcription + AiPane** - Write
      `src/pages/NewSummaryPage/TranscribeSection.tsx` and
      `src/pages/NewSummaryPage/AiPane.tsx` (wraps 11a's `Tabs` with
      Transcript/Summary panels). `NewSummaryPage` renders `AiPane` once a
      transcript exists, the existing empty-state placeholder until then.
      *Done when:* transcribing a real trimmed clip (either method available
      in this dev environment) completes, the transcript appears in the
      Transcript tab, switching to the Summary tab and back works, and the
      Summarize section is hidden when the transcript text is empty (a
      silent/very short clip) and shown otherwise.
- [x] **Step 4 - Summarization** - Write
      `src/pages/NewSummaryPage/SummarizeSection.tsx`; extend `AiPane` to
      show the latest summary in the Summary tab. *Done when:* summarizing a
      real transcribed clip (with a provider that has a configured API key in
      `.env`) completes and its content appears in the Summary tab - this
      completes New Summary parity end to end (download through summarize).

## Files / areas

- `frontend-react/src/App.tsx` - `"new-summary"` branch replaced with
  `<NewSummaryPage />`.
- `frontend-react/src/hooks/usePolling.ts`, `useWaveform.ts` - new.
- `frontend-react/src/pages/NewSummaryPage/` - new: `NewSummaryPage.tsx`,
  `DownloadSection.tsx`, `TrimSection.tsx`, `TranscribeSection.tsx`,
  `SummarizeSection.tsx`, `AiPane.tsx`.
- `frontend-react/package.json` - adds `wavesurfer.js`.
- No changes to `backend/`, `frontend/`, or 11a's shared
  `components/shared/`, `components/layout/`, `api/`, `lib/` files (consumed,
  not modified).

## Data / contracts

Locked so 11b's build matches today's app exactly, and so 11c can reuse the
same pieces:

- `usePolling<T extends PollableStatus>({ key, intervalMs = 2000, fetchStatus,
  onDone, onError })` - `key` is the video id (or `null` to stay idle); the
  effect restarts whenever `key` changes and tears down its timer on
  cleanup. A thrown/rejected `fetchStatus` call is caught and passed to
  `onError` as `{ status: "error", error: <message> }`, never left unhandled.
- wavesurfer config, ported exactly from `frontend/js/app.js:188-224`:
  `waveColor: "#8A7A6A"`, `progressColor: "#C96F45"`, `cursorColor:
  "#3A2A1E"`, `height: 96`, region added on `"decode"` spanning the full
  duration (`color: "rgba(201, 111, 69, 0.2)"`, `drag: true`, `resize:
  true`), `SKIP_SECONDS = 5`. Audio URL is `audioUrl(videoId)` (11a's API
  client) with a cache-busting query param that changes on every
  render/re-render (matching today's `?t=${Date.now()}` on both initial load
  and post-trim reload).
- Empty-transcript copy is exactly `"No speech detected in this clip."`,
  matching `showTranscript`'s existing string - don't reword it.
- Default radio selections: transcription method defaults to **API**,
  summary provider defaults to **Anthropic** - matching the `checked`
  attributes in today's markup exactly (do not default to Local/OpenAI).
- Section container styling: `rounded-lg bg-ivory p-6 dark:bg-near-black
  dark:border dark:border-warm-gray/30` with a `font-serif text-xl
  font-semibold` heading - reuse this pattern across all four sections rather
  than inventing new section chrome.

## Testing

- No new pure/branching logic is introduced beyond what 11a already covers
  (`nextPollAction`, `formatTime` are reused as-is); `usePolling` and
  `useWaveform` are integration/effects code (timers, DOM, a third-party
  library), so per `coding-standards.md`'s testing gate they ride on real
  browser verification against the running backend, not new Vitest files.
  If a step turns up a genuinely branching pure function that isn't already
  covered (there isn't one expected here), add a focused test for it then.
- Run `npm test` once at the end of this feature to confirm 11a's existing
  suite is still green, and `pytest` to confirm the unchanged backend is
  still green.
- Each step's manual verification runs against the real backend
  (`uvicorn backend.main:app --reload`) with a real short YouTube URL end to
  end, the same way Phase 1's original build verified downloads - not
  mocked, since this is proving the new frontend against the real API
  surface it will ship against.

## Notes for the AI

- Phase 11 planning sketched a `useNewSummaryPipeline` reducer/state-machine
  for this page. Building it now, a plain handful of `useState` calls in
  `NewSummaryPage` covers the same "one source of truth for video id and
  phase" goal with less machinery - prefer that; don't introduce a reducer
  the actual scope doesn't need.
- `usePolling`'s error-catching requirement isn't hypothetical: the branch
  just merged (`feat: error messages for failed API calls`) exists
  specifically because the old app's poll loops could fail silently. Don't
  reintroduce that gap in the rewrite.
- Keep `useWaveform`'s region data in a ref for click-time reads (Preview/Trim
  need the current region when clicked), but it's fine for the visible
  Start/End labels to come from `useState` updated on `"region-updated"` -
  the labels are two small text nodes, not a performance concern, so this
  doesn't need the same ref-only treatment as the click-time reads.
- Destroy the previous wavesurfer instance before creating the next one
  (on both initial mount and post-trim reload), and verify no console errors
  or leaked `AudioContext`s after trimming the same clip several times in a
  row.
- `AiPane` and its Transcript/Summary content are New Summary's
  single-latest-summary shape - don't build this as something 11c's
  full-history Library view will also consume; those are deliberately
  different shapes sharing only the `Tabs` chrome (per 11a's contract).

## Verification evidence

- `npm run build`, `npm run lint`, `npm test` (16/16 passing) - all clean in
  `frontend-react/`.
- `pytest` - 89/89 passing, backend unchanged.
- Playwright against the real running backend with a real short YouTube URL
  (`jNQXAC9IVRw`, "Me at the zoo"): Preview shows title/channel/duration;
  invalid URL surfaces the backend's real error via `AsyncStatus`; a mocked
  long-duration metadata response shows the warning banner and requires
  Confirm & Download; Download completes via `usePolling` and reveals Trim.
- Waveform renders and is draggable; Play/Pause, both skip buttons, and
  Preview all work; trimmed the same clip 3 times in a row with zero console
  errors (no AudioContext leak); dragging the region under 1 second and
  trimming surfaces the backend's real "Trim range must be at least 1
  second." validation error via `AsyncStatus`.
- Transcription (API method, default-checked) produced a real transcript
  shown in the Transcript tab; Transcript/Summary tab switching works; a
  mocked empty-transcript response shows "No speech detected in this clip."
  and hides the Summarize section entirely.
- Summarization (OpenAI - the only provider with a real key in this
  environment's `.env`; Anthropic's is empty) produced a real summary shown
  in the Summary tab, no console errors.
- Starting a second download resets trim/transcript/summary state, so a
  fresh download doesn't leave stale sections from a prior run (the
  intentional correctness fix flagged in scope, not a regression).
- Targeted audit of the diff found no P0/P1 issues. One new P2 finding
  logged (`F-08`, trimming the default full-duration region can hit a real
  backend 400 due to a float/int duration mismatch) - verified as an exact
  port of a pre-existing latent bug already in `frontend/js/app.js`, not a
  regression, left for a future `/fix` rather than diverging from parity.
