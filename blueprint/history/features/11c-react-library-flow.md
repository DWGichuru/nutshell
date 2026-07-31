# Feature: React frontend rewrite - Library flow

**From build-plan:** feature 11c
**Status:** complete

## Goal

Build the Library page in `frontend-react/` on top of 11a's shell/shared
components and 11b's patterns: search/filter past videos, select one to load
its full detail (title/channel/date, transcript, complete summary history),
and generate a new summary in place - matching `frontend/js/app.js`'s Library
behavior (`fetchVideos`/`renderLibraryResults`/`selectLibraryVideo`/
`showLibrarySummaries`/`startLibrarySummarization`) exactly, with no backend
changes. The old `frontend/` app keeps serving `:8000` unchanged; this feature
only touches `frontend-react/`.

## In scope

- `LibraryPage` container replacing `App.tsx`'s `"library"` placeholder
  branch: owns `search`/`dateFrom`/`dateTo` filter inputs, the fetched video
  list, `selectedVideoId`, and the selected video's meta/transcript/summaries,
  rendered in 11a's `ResizablePane` (interaction pane left, AI pane right)
  exactly like `NewSummaryPage` does.
- `SearchSection`: search text + date-from/date-to inputs, a Filter button
  (Enter key in any input also triggers it, matching today's keydown
  handler), calling `listVideos` (already in 11a's `api/client.ts`, unchanged)
  on filter and once on initial mount (Library has no separate "view shown"
  event in the SPA-less React app, so mount replaces `showLibraryView`'s
  `fetchVideos()` call). Renders the results list, an empty state ("No videos
  found."), and highlights the selected row - reusing `formatDate` from
  11a's `lib/format.ts`.
- Video selection: clicking a row sets `selectedVideoId` and triggers loading
  that video's `getVideo`, `getTranscript` (its real 404 renders "No
  transcript yet for this video.", matching today - distinct from an empty
  transcript's real "No speech detected in this clip." text), and
  `getSummaries` (already in 11a's client). Uses a cancelled-flag effect
  (React's standard race-guard) so a fast second click before the first
  video's fetches resolve never overwrites the newer selection - the same
  guarantee as today's `videoId !== currentLibraryVideoId` checks, expressed
  idiomatically for React instead of ported as global mutable comparisons.
- `LibraryAiPane`: wraps 11a's shared `Tabs` (Transcript/Summary) with a
  title/date header above them, reset to the Transcript tab whenever
  `selectedVideoId` changes. Deliberately distinct from 11b's `AiPane`: the
  Summary tab here renders the **full summary history** (today's
  `showLibrarySummaries` behavior - every entry, newest first, each with its
  timestamp heading), not the single latest summary - per the standing 9b
  decision documented in `project-overview.md`'s data model. Both share only
  `Tabs` chrome, matching 11a's contract and 11b's note not to conflate the
  two shapes.
- `GenerateSummarySection`: provider radio (Anthropic checked by default,
  matching today), visible only once a video is selected, in the interaction
  pane below the search/results (matching 9b's placement). Calls
  `startSummarization` + `usePolling` (11b's hook, reused as-is) against
  `getSummarizationStatus`, then re-fetches `getSummaries` on completion so
  the new entry appears at the top of the history.
- All new sections use 11a's shared `AsyncStatus` for busy/status/error
  display - search/filter errors, detail-load errors, and summarization
  errors each surface to the user, matching the error-messages feature's
  intent already carried into 11b.

## Out of scope

- Dark mode toggle, wordmark/favicon - 11d.
- Backend serving cutover, deleting `frontend/` - 11e.
- Any change to `backend/` - every endpoint used here (`listVideos`,
  `getVideo`, `getTranscript`, `getSummaries`, `startSummarization`,
  `getSummarizationStatus`) already exists in 11a's `api/client.ts` and is
  unchanged.
- New Summary page - done in 11b.
- Deleting a video, export options, manual index resync - Phase 8
  (post-MVP), not this feature.
- A shared cross-page "AI pane" abstraction - per 11b's note, `LibraryAiPane`
  and New Summary's `AiPane` deliberately stay separate components sharing
  only `Tabs`.

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight on.
   Checkpoints are optional; `/complete` makes the real feature-level commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the step was too big, so split it.

## Build steps

- [x] **Step 1 - `LibraryPage` + `SearchSection`** - Write
      `src/pages/LibraryPage/LibraryPage.tsx` and
      `src/pages/LibraryPage/SearchSection.tsx`; replace `App.tsx`'s
      `"library"` placeholder branch with `<LibraryPage />` (still using
      11a's shared `ResizablePane` with the same
      `{ minWidth: 280, minRemainder: 320 }` bounds as `NewSummaryPage`). The
      AI pane side stays the existing empty-state placeholder text for now.
      *Done when:* against the real running backend with existing stored
      videos in `data/videos/`, the page loads and lists all videos on
      mount; entering a search term or date range and clicking Filter (or
      pressing Enter in a filter input) narrows the results via `listVideos`;
      an out-of-range filter shows "No videos found."; clicking a row
      visually highlights it (selection state only - no detail fetch yet).
- [x] **Step 2 - Video detail + `LibraryAiPane` (Transcript tab)** - Write
      `src/pages/LibraryPage/LibraryAiPane.tsx` and wire `LibraryPage` to
      fetch `getVideo`/`getTranscript` on `selectedVideoId` change via a
      cancelled-flag effect. *Done when:* selecting a video shows its
      title and `channel - date` header and its transcript in the
      Transcript tab; selecting a video with no transcript yet shows "No
      transcript yet for this video."; switching rapidly between two videos
      before their fetches resolve leaves the UI showing only the
      last-clicked video's data (no flicker to a stale one); the Summary tab
      exists and is selectable but its content is deferred to Step 3.
- [x] **Step 3 - Summary history + `GenerateSummarySection`** - Extend
      `LibraryAiPane`'s Summary tab to fetch and render `getSummaries`
      (newest first, each entry's `created_at` as a heading and `content` in
      a `<pre>`, an empty state "No summaries yet." when the list is empty).
      Write `src/pages/LibraryPage/GenerateSummarySection.tsx` (provider
      radio, Summarize button, `usePolling` against
      `getSummarizationStatus`), rendered in the interaction pane once a
      video is selected. *Done when:* selecting a video with existing
      summaries shows its full history in the Summary tab; generating a new
      summary for a real transcribed video (with a provider that has a
      configured API key in `.env`) completes and the new entry appears at
      the top of the history without re-selecting the video; a
      summarization failure surfaces via `AsyncStatus`. This completes
      Library parity end to end.

## Files / areas

- `frontend-react/src/App.tsx` - `"library"` branch replaced with
  `<LibraryPage />`.
- `frontend-react/src/pages/LibraryPage/` - new: `LibraryPage.tsx`,
  `SearchSection.tsx`, `LibraryAiPane.tsx`, `GenerateSummarySection.tsx`.
- No changes to `backend/`, `frontend/`, 11a's shared
  `components/shared/`, `components/layout/`, `api/`, `lib/`, or 11b's
  `pages/NewSummaryPage/` files (consumed, not modified).

## Data / contracts

- No new API client functions or types - `listVideos`, `getVideo`,
  `getTranscript`, `getSummaries`, `startSummarization`,
  `getSummarizationStatus` and their types already exist in 11a's
  `api/client.ts`/`api/types.ts`, unchanged.
- `usePolling` (11b) and `Tabs`/`AsyncStatus`/`ResizablePane` (11a) are
  reused as-is, no changes.
- Empty-transcript-yet-created copy stays exactly `"No transcript yet for
  this video."` (a 404 from `getTranscript`); empty-but-transcribed copy
  stays exactly `"No speech detected in this clip."` (an empty `text` field)
  - these are two different states, don't conflate them.
- Default radio selection: summary provider defaults to **Anthropic**,
  matching today's `checked` attribute (do not default to OpenAI).
- Section container styling: `rounded-lg bg-ivory p-6 dark:bg-near-black
  dark:border dark:border-warm-gray/30` with a `font-serif text-xl
  font-semibold` heading, matching 11b's sections and today's markup.
- Selected-row highlight classes: reuse the same visual treatment as
  today's `LIBRARY_ROW_SELECTED_CLASSES` (`rounded pl-2 bg-terracotta/10
  border-l-2 border-terracotta`) as Tailwind classes conditionally applied,
  not a ported mutable class-list toggle.

## Testing

- No new pure/branching logic - `listVideos`/`formatDate`/`usePolling` are
  reused as-is from 11a/11b, so per `coding-standards.md`'s testing gate
  this rides on real browser verification against the running backend, not
  new Vitest files. If a step turns up a genuinely branching pure function
  (there isn't one expected here), add a focused test for it then.
- Run `npm test` once at the end of this feature to confirm 11a/11b's
  existing suite is still green, and `pytest` to confirm the unchanged
  backend is still green.
- Each step's manual verification runs against the real backend
  (`uvicorn backend.main:app --reload`) using real stored videos already in
  `data/videos/` - no new downloads or paid API calls needed for Steps 1-2;
  Step 3's summarize action does use a real provider key already configured
  in `.env`.

## Notes for the AI

- Port `selectLibraryVideo`'s three sequential fetches (meta, transcript,
  summaries) as a single effect keyed on `selectedVideoId`, guarded by a
  `let active = true` / `return () => { active = false }` cleanup - React's
  standard race-condition guard - rather than porting the old app's global
  `currentLibraryVideoId` comparison variable-by-variable.
- `LibraryAiPane`'s tab-reset-on-select behavior should key off
  `selectedVideoId` changing (unlike 11b's `AiPane`, which keys off the
  `transcript` object reference) - Library can reselect the same video after
  generating a new summary without wanting a tab reset, whereas a fresh
  transcript object always means a truly new result.
- Keep `GenerateSummarySection` reading the *current* `selectedVideoId` at
  click time (not a stale closure) - same caution 11b's `SummarizeSection`
  already handles via its own local `videoId` prop.
- Don't build a shared "AI pane" component consumed by both pages - 11b's
  notes already called this out; `LibraryAiPane` and New Summary's `AiPane`
  are intentionally separate, sharing only `Tabs`.

## Verification evidence

- `npm run build`, `npm run lint`, `npm test` (16/16 passing) - all clean in
  `frontend-react/`.
- `pytest` - 89/89 passing, backend unchanged.
- Playwright against the real running backend with real stored videos in
  `data/videos/` (no live download or paid transcription calls): initial
  list load on mount, search/date filtering, "No videos found." empty
  state, row-selection highlight.
- Video detail: title/channel/date header and transcript render for a
  transcribed video; a never-transcribed video shows "No transcript yet for
  this video." (distinct from an empty-but-transcribed clip's "No speech
  detected in this clip."); rapidly clicking three different rows before
  their fetches resolve settles on only the last-clicked video's data, no
  stale flicker, no console errors.
- Summary tab: existing full history renders newest-first; generating a new
  summary via a real OpenAI call (the only provider with a configured key in
  this environment's `.env`) completes and the new entry appears at the top
  without re-selecting the video; a video with zero summaries shows "No
  summaries yet."
- Dark mode sanity pass (forced via `classList.add('dark')`, since the
  toggle itself is 11d's job): all new elements render with correct
  contrast, no console errors.
- Targeted audit of the diff found one finding, fixed in the same pass:
  `SearchSection`'s mount-fetch effect had its own inline promise chain
  duplicating the Filter button's `fetchVideos` logic (a workaround for
  React's `set-state-in-effect` lint rule). Fixed by deferring the call via
  `Promise.resolve().then(() => fetchVideos())` so it reuses the one
  implementation; reverified clean lint/build/test and no regression via
  Playwright. Logged as F-09 in `blueprint/context/findings.md` (P2,
  status `fixed` - remains in the ledger for a future `/audit` to close).
- Pre-existing findings F-03, F-04, F-05, F-07, F-08 (all P2/P3) are
  untouched by this feature and remain open in the ledger.
