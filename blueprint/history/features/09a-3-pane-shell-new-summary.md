# Feature: 3-pane shell + New Summary flow

**From build-plan:** feature 9a
**Status:** complete

## Goal

Replace the top nav bar with a persistent left drawer, and restructure the New
Summary flow into a 3-pane shell: the existing forms/actions in a fixed-width
interaction pane, and a new tabbed AI-generated pane (Transcript, Summary) that
shows generated content. This is the first of two sub-features under Phase 9;
Library stays in its current layout until 9b unifies it into the same shell.

## Design reference

- `prototypes/new-summary.html` - Start and In-progress states for exactly this
  page, with a working state/tab toggle for browser preview.
- `prototypes/theme.css` - documents the palette/spacing as CSS variables, but
  it's a 1:1 port of the colors already in `frontend/index.html`'s Tailwind
  config (terracotta/cream/ivory/espresso/warm-gray/near-black) and the
  `font-serif`/`font-sans` utility classes already used there. **No Tailwind
  config changes or token porting needed** - build directly with the existing
  utility classes, using arbitrary-value width classes (e.g. `w-[232px]`,
  `w-[420px]`) to match the drawer/interaction-pane widths in `theme.css`.
- Per the approved mockup, the current `<header>` wordmark moves into the
  drawer; the tagline paragraph ("Paste a YouTube link...") is dropped, since
  the mockup's drawer has no room for it and the nav items make the app's
  purpose clear enough on their own.

## In scope

- A persistent left drawer (wordmark + New Summary / Library nav items),
  replacing the current top nav bar, visible regardless of which page is active.
- Restructuring `new-summary-view` into two panes: the existing
  download/trim/transcribe/summarize sections (unchanged behavior) in a
  fixed-width interaction pane, and a new tabbed AI-generated pane (Transcript
  tab, Summary tab) beside it.
- Moving the existing `transcript-display` and `summary-display` elements into
  the new AI-generated pane's tabs, with the same content, populated by the
  same existing fetch calls - just relocated, not changed.
- An empty state for the AI-generated pane before any transcript exists,
  matching the mockup's placeholder text.
- Dark mode support on every new/moved element, matching existing `dark:`
  patterns.

## Out of scope

- Migrating the Library page into this shell (9b).
- A collapsible/toggleable drawer - it's persistent-only per the earlier
  decision.
- Any new colors, fonts, or Tailwind config changes - palette is unchanged.
- Multiple summary-format tabs or a summary run history - the Summary tab
  shows the current/most recent summary only, per the earlier decision.
- Any backend or API changes - this is frontend-only.
- Responsive/mobile layout - desktop-only, matching the rest of the app.

## Build steps

- [x] **Step 1 - Persistent drawer**
- [x] **Step 2 - Interaction pane + empty AI pane scaffold**
- [x] **Step 3 - Transcript tab**
- [x] **Step 4 - Summary tab**

## Files / areas

- `frontend/index.html` - drawer, interaction pane, AI-generated pane markup.
- `frontend/js/app.js` - view-toggle target elements, tab-switch logic,
  `showTranscript()`/`showLatestSummary()` target updates.

## Data / contracts

- None. No backend routes, request/response shapes, or stored data change.

## Testing

- No new pure logic - DOM restructuring plus small event-handler wiring. Rode
  on browser evidence per the testing gate, not new pytest tests.
- `pytest`: 89 passed (no backend files touched, run as a regression check).

## Completion evidence

- Playwright, light + dark mode, at every step: drawer persistence and nav
  toggle, pane layout, empty AI-pane placeholder, Transcript tab (real stored
  transcript data from an existing video), Summary tab (real stored summary
  data, including the "loaded while viewing the other tab" case), and the
  silent/empty-transcript edge case. No console/page errors observed.
- No live `yt-dlp` download or paid summarization/transcription API call was
  run - this feature only changes where results are displayed, not the
  download/trim/transcribe/summarize request logic, and every changed code
  path (`showTranscript`, `showLatestSummary`, `setActiveAiTab`) was exercised
  against real stored data from existing videos in `data/videos/`.

## Findings

Self-review during the build surfaced one bug directly in this feature's new
component, repaired in-branch:

- Drawer nav active state didn't override the inactive dark-mode classes
  (`INACTIVE_NAV_CLASSES` was missing the `dark:bg-espresso/60`/
  `dark:text-cream` classes hard-coded onto `nav-library`, so Tailwind's
  higher-specificity `dark:` rules always won the cascade over the JS-added
  `bg-terracotta`). Pre-existing in the old top-nav, but far more visible in
  the persistent drawer. Fixed by widening `INACTIVE_NAV_CLASSES`; verified via
  screenshot. Not added to the ledger as a separate entry since it was found
  and repaired within this same feature's build, not by a subsequent `/audit`
  pass.

The pre-existing P2/P3 ledger entries (duplicate status-tracking pattern,
unvalidated `video_id` path segments, duplicate frontend error/poll helpers,
plus the new placeholder-truncation-at-420px follow-up) remain open in
`blueprint/context/findings.md` for future work; none are P0/P1 and none
block this completion.
