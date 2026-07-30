# Feature: React frontend rewrite - scaffold + shared hooks/components

**From build-plan:** feature 11a
**Status:** complete

## Goal

Stand up a React + TypeScript + Vite + Tailwind app in a new `frontend-react/`
directory - the foundation the rest of the Phase 11 rewrite builds on - without
touching the current running app. Delivers the empty 3-pane shell (top bar,
drawer, page switch) styled to match today's app, plus the shared building
blocks (typed API client, pure helper functions with tests, and the
Tabs/AsyncStatus/ResizablePane components) that 11b (New Summary flow) and 11c
(Library flow) will consume. The old `frontend/index.html` + `frontend/js/app.js`
keep serving the live app at `:8000`, untouched, throughout this feature and all
of 11b/11c/11d - only 11e (cutover) replaces them.

## In scope

- Vite + React + TypeScript scaffold in `frontend-react/` (sibling to
  `frontend/`, not nested inside it), with Tailwind v3 configured to match the
  current app's palette and `darkMode: "class"` setting exactly.
- A dev workflow: `npm run dev` (Vite on `:5173`) proxying `/api/*` to the
  FastAPI dev server on `:8000`, so the new app can call the real backend
  during development with no backend changes.
- Vitest added as an explicit test runner (not a silent install), wired to
  `package.json` and documented in `AGENTS.md`'s Commands section.
- A typed API client (`src/api/types.ts` + `src/api/client.ts`) covering every
  endpoint under `/api/videos` used anywhere in the Phase 11 rewrite (this
  feature doesn't call most of them yet - 11b/11c do - but the client is
  written once, completely, here so later features only import it).
- Pure helper functions with unit tests: time/date formatting, resizable-pane
  width-clamping math, and the poll-response-to-next-action decision function.
- Shared, reusable components: `Tabs` (tab-header chrome only, no content
  opinion), `AsyncStatus` (spinner + status text + error banner), and
  `ResizablePane` (wrapping a `useResizablePane` hook).
- The empty shell: `TopBar` (plain-text "Nutshell" heading for now - the real
  wordmark/favicon come in 11d) + `Drawer` (New Summary / Library nav buttons)
  + an `activePage` toggle switching between two placeholder `<main>` panes,
  each already wrapped in `ResizablePane` with dummy content, so the divider is
  visibly working even though no real page content exists yet.

## Out of scope

- Calling any endpoint beyond what's needed to prove the API client compiles
  and types check - no download/trim/transcribe/summarize/library UI yet
  (11b, 11c).
- `usePolling` and `useWaveform` hooks - deferred to 11b, since they have no
  caller until the New Summary flow exists. (`useResizablePane` is needed now
  for the shell; `useDarkMode`'s hook and toggle UI are deferred to 11d.)
- Dark mode toggle UI, wordmark/favicon assets - 11d.
- Any change to `backend/main.py`, `frontend/index.html`, or `frontend/js/` -
  the old app keeps serving `:8000` unchanged until 11e's cutover.
- ESLint/Prettier beyond a minimal typescript-eslint + eslint-plugin-react-hooks
  setup - no style-only tooling beyond what catches real bugs (e.g. missing
  effect dependencies).

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight on.
   Checkpoints are optional; `/complete` makes the real feature-level commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the step was too big, so split it.

## Build steps

- [x] **Step 1 - Scaffold + Tailwind config + empty shell** - `npm create
      vite@latest frontend-react -- --template react-ts`, install Tailwind v3 +
      PostCSS + Autoprefixer, port the exact palette from
      `frontend/index.html`'s inline `tailwind.config` (terracotta `#C96F45`,
      terracotta-dark `#A85A38`, cream `#F5F1EA`, ivory `#F0E0C8`, espresso
      `#3A2A1E`, warm-gray `#8A7A6A`, near-black `#1E1B16`, sage `#3D5A3D`, rust
      `#B5533C`, `darkMode: "class"`) into `tailwind.config.js`. Add
      `vite.config.ts` with `server.proxy: { "/api": "http://localhost:8000" }`.
      Add minimal ESLint (typescript-eslint + eslint-plugin-react-hooks).
      `App.tsx` renders `TopBar` (plain-text heading + hamburger button) +
      `Drawer` (New Summary / Library nav buttons, `.hidden`-equivalent
      collapse behavior) + an `activePage` state toggling between two empty
      placeholder `<main>` blocks. *Done when:* `npm run dev` serves the shell
      at `:5173`; a side-by-side screenshot against the live app at `:8000`
      shows matching background/text/border colors, fonts, top bar layout, and
      drawer toggle behavior in light mode.
- [x] **Step 2 - Vitest setup + pure lib helpers** - Add Vitest (`npm install
      -D vitest`, a `"test": "vitest run"` script), and update `AGENTS.md`'s
      Commands section to list the new `npm run dev`, `npm run build`, and
      `npm test` commands alongside the existing `uvicorn`/`pytest` lines.
      Write `src/lib/format.ts` (`formatTime(seconds: number): string`,
      `formatDate(iso: string): string`), `src/lib/pane-math.ts`
      (`clampWidth`, `computeMaxWidth` - see contracts), and
      `src/lib/polling.ts` (`nextPollAction(response: {status: string; error?:
      string | null}): "done" | "error" | "continue"`). *Done when:* `npm test`
      passes with unit tests covering each function's edge cases (zero
      seconds, malformed/empty date, a clamp where raw width is below min and
      above max, each of the three `nextPollAction` branches).
- [x] **Step 3 - Typed API client** - Write `src/api/types.ts` mirroring every
      model in `backend/models.py` field-for-field (see Data / contracts
      below) and `src/api/client.ts` with one typed function per
      `/api/videos` endpoint. Nothing calls this client yet - it only needs to
      compile and type-check cleanly. *Done when:* `tsc --noEmit` (or the
      Vite/ESLint build) passes with no type errors, and every field in
      `src/api/types.ts` is verified 1:1 against `backend/models.py`.
- [x] **Step 4 - Shared components: Tabs, AsyncStatus, ResizablePane** - Write
      `useResizablePane(options: {minWidth: number; minRemainder: number})`
      (pointer-event wiring in a `useEffect`, using the pure `clampWidth`/
      `computeMaxWidth` from Step 2) and a `ResizablePane` component wrapping
      it. Write `Tabs` (presentational tab-header, no content opinion) and
      `AsyncStatus` (`busy`, `statusText`, `error` props rendering a
      spinner/status-text/error-banner triplet). Wire `ResizablePane` into both
      placeholder panes from Step 1 with `minWidth: 280, minRemainder: 320`
      (matching `frontend/js/app.js`'s existing `makeResizablePane` calls
      exactly) and dummy content so the divider is visibly draggable. *Done
      when:* dragging either view's divider resizes both panes and stops at
      the 280px/320px-remainder bounds, matching the current app's resize
      behavior at `:8000` side by side.

## Files / areas

- `frontend-react/` (new directory) - `vite.config.ts`, `tailwind.config.js`,
  `tsconfig.json`, `src/main.tsx`, `src/App.tsx`, `src/api/types.ts`,
  `src/api/client.ts`, `src/lib/format.ts`, `src/lib/pane-math.ts`,
  `src/lib/polling.ts`, `src/hooks/useResizablePane.ts`,
  `src/components/layout/TopBar.tsx`, `src/components/layout/Drawer.tsx`,
  `src/components/shared/Tabs.tsx`, `src/components/shared/AsyncStatus.tsx`,
  `src/components/shared/ResizablePane.tsx`.
- `AGENTS.md` - Commands section gets the new npm scripts.
- No changes to `frontend/`, `backend/`, or any existing file's behavior.

## Data / contracts

Load-bearing shapes 11b/11c will depend on - lock these now:

- `src/api/types.ts` mirrors `backend/models.py` exactly: `MetadataRequest
  {url: string}`, `VideoMetadataResponse {title: string; channel: string;
  duration_seconds: number; needs_confirmation: boolean; estimated_minutes:
  number | null}`, `VideoMeta {video_id, title, channel, duration_seconds,
  date_added, source_url: string}`, `DownloadStartedResponse {video_id:
  string; status: string}`, `DownloadStatusResponse {status: string; error?:
  string | null}`, `TrimRequest {start_seconds: number; end_seconds: number}`,
  `TrimResponse {status: string; duration_seconds: number}`,
  `TranscriptSegment {start: number; end: number; text: string}`,
  `Transcript {text: string; segments: TranscriptSegment[]; method: "local" |
  "api"}`, `TranscribeRequest {method: "local" | "api"}`,
  `TranscriptionStartedResponse`/`TranscriptionStatusResponse` (same shapes as
  the download equivalents), `SummarizeRequest {provider: "anthropic" |
  "openai"}`, `SummarizationStartedResponse`/`SummarizationStatusResponse`
  (same shapes again), `SummaryEntry {created_at: string; content: string}`,
  `SummaryListResponse {summaries: SummaryEntry[]}`, `VideoSummary {video_id,
  title, channel, duration_seconds, date_added: string}`, `VideoListResponse
  {videos: VideoSummary[]}`.
- `nextPollAction(response)` returns `"done"` when `response.status === "done"`,
  `"error"` when `response.status === "error"`, `"continue"` otherwise - this
  exact contract is what 11b's `usePolling` hook will be built against.
- `useResizablePane`'s `minWidth`/`minRemainder` values are `280`/`320` for
  both views, matching `frontend/js/app.js:789-790` exactly - do not change
  these without updating both the old and new app in the same step.

## Testing

- `pytest` (backend) is unaffected by this feature and should stay green, but
  isn't touched by it.
- This is the feature that introduces the frontend test runner: `npm test`
  (Vitest) becomes the gate for this project's genuinely pure logic going
  forward, per `coding-standards.md`'s testing philosophy. Step 2 ships tests
  for every function in `src/lib/` (formatting, pane-math clamping, poll
  decision logic) - these are plain input/output functions with real edge
  cases, exactly what the gate calls for.
- Step 1 and Step 4 are shell/layout and UI-wiring, not new pure logic (the
  pane math Step 4 uses is already tested in Step 2) - verified via a
  screenshot comparison against the live app at `:8000` and a manual
  divider-drag check, not new unit tests. Step 3 is a typed data-shape mirror
  with no branching logic of its own - verified by type-checking cleanly, not
  a unit test.
- Run `npm test` once at the end of this feature to confirm the full frontend
  suite is green, alongside the existing `pytest` for the untouched backend.

## Notes for the AI

- `frontend-react/` is a new sibling directory, not nested inside `frontend/`
  and not replacing it yet - `frontend/index.html` and `frontend/js/app.js`
  must keep working exactly as they do today throughout this entire feature.
  Don't touch `backend/main.py`'s static-serving setup; that's 11e's job.
- Keep the Tailwind palette copy verbatim from `frontend/index.html`'s inline
  `tailwind.config` script - don't approximate colors from the design doc's
  hex table when the actual inline config is available to copy directly, in
  case of any subtle formatting differences.
- `Tabs` should own only the tab-header chrome (active/inactive styling,
  click-to-switch) and take its content as children/props - do not build in
  an opinion about what the tab content looks like, since 11b's single-latest-
  summary view and 11c's full-history-list view are genuinely different shapes
  that both sit under this same tab-header component.
- No router library - `activePage` is a single piece of state in `App.tsx`
  (`"new-summary" | "library"`), matching today's `.hidden`-class-toggle
  behavior with no deep-linking.
- Keep ESLint minimal; don't add Prettier or other style-only tooling unless
  asked.

## Verification evidence

- `npm run build`, `npm run lint`, `npm test` (16/16 passing) - all clean in
  `frontend-react/`.
- `pytest` - 89/89 passing, backend unaffected.
- Playwright screenshot comparisons against the live app at `:8000`: palette,
  fonts, top bar, and drawer nav styling matched; drawer collapse and
  active-nav swap confirmed; divider drag confirmed on both pages including
  the 280px min-width and `container - 320px remainder` max-width clamps.
