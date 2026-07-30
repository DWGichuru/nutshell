# Feature: Unify Library into the 3-pane shell

**From build-plan:** feature 9b
**Status:** complete

## Goal

Move Library's search/filter/results into a fixed-width interaction pane
(matching New Summary's pattern from 9a), and its transcript/summaries/generate-
summary form into a tabbed AI-generated pane (Transcript, Summary), retiring the
old single-column `library-detail-section` card. This completes Phase 9: both
pages now share the same 3-pane shell.

## Design reference

- `prototypes/library.html` - List and Detail states for exactly this page,
  with a working state/tab toggle for browser preview.
- `prototypes/theme.css` - same palette/spacing reference as 9a; still no
  Tailwind config changes needed, build with the existing utility classes
  established in 9a (`w-[420px]` interaction pane, the `ai-tab-*`/`ai-pane-*`
  chrome pattern).
- Per the earlier clarifying decision (this session), Library's Summary tab
  keeps showing the **full history** of past summary runs (today's
  `showLibrarySummaries()` behavior), unlike New Summary's single-latest-summary
  tab - this is a deliberate deviation from the generic AI-pane decision, since
  browsing past runs is Library's core existing value and is documented in
  `project-overview.md`'s data model ("multiple summary runs... all preserved").
- The mockup highlights the selected row in the results list and shows the
  "Generate new summary" form only once a video is selected - both included
  below.

## In scope

- Wrap `library-search-section` (search/filter inputs + results list) in a
  fixed-width interaction pane, matching the New Summary pane's width/spacing.
- Highlight the currently-selected row in the results list (matching the
  mockup), tracked via the existing `currentLibraryVideoId`.
- A Library-scoped AI-generated pane (empty state + tabbed populated state:
  Transcript, Summary), separate DOM/ids from New Summary's `ai-pane` (same
  visual pattern, not shared elements - matches how the interaction pane's
  sections are already page-specific, not shared).
- Moving `library-detail-title`/`library-detail-meta` into a small header above
  the tabs in that pane, and `library-transcript-display` into the Transcript
  tab - same ids, same content logic, relocated only.
- Moving the summaries list (`library-summaries`) into the Summary tab - same
  id, same content logic (full history), relocated only.
- Moving the "Generate new summary" form (provider/format pickers, button,
  status/spinner/error) into the interaction pane, visible only once a video is
  selected.
- Retiring `library-detail-section`'s old card styling once its content has
  moved elsewhere.
- Dark mode support on every new/moved element, matching existing `dark:`
  patterns and the fix already applied to the drawer nav in 9a.

## Out of scope

- Any changes to the New Summary page - it's done (9a).
- Any backend or API changes - frontend-only, same as 9a.
- A collapsible drawer - still persistent-only.
- Responsive/mobile layout - desktop-only, matching the rest of the app.
- Consolidating the New-Summary and Library tab-switch logic into one shared
  helper - this feature follows the existing pattern of parallel,
  page-specific functions (like `setActiveAiTab` from 9a), consistent with how
  the rest of the codebase already duplicates per-section error/poll helpers
  (tracked as F-05 in the findings ledger, not this feature's job to fix).
- Deleting `prototypes/` - this is the last feature consuming it
  (`library.html`), so `/complete` should discard the folder once 9b is done,
  not a build step here.

## Build steps

- [x] **Step 1 - Library interaction pane + untabbed AI pane scaffold**
- [x] **Step 2 - Transcript/Summary tabs**
- [x] **Step 3 - Move the generate-summary form into the interaction pane**
- [x] **Step 4 - Selected-row highlight, retire old card styling, final polish**

## Files / areas

- `frontend/index.html` - Library interaction pane, Library AI-generated pane
  markup, generate-summary form relocation.
- `frontend/js/app.js` - `selectLibraryVideo()` updates, new
  `setActiveLibraryAiTab()`/`activeLibraryAiTab`, `showLibrarySummaries()` and
  `startLibrarySummarization()` target/visibility updates, selected-row
  highlighting in `renderLibraryResults()`.

## Data / contracts

- None. No backend routes, request/response shapes, or stored data change.

## Testing

- No new pure logic - DOM restructuring plus event-handler wiring, same as 9a.
  Rode on browser evidence per the testing gate, not new pytest tests.
- `pytest`: 89 passed at every step (no backend files touched).

## Completion evidence

- Playwright, light + dark mode, at every step, using real stored data from
  existing videos in `data/videos/` (no live download or paid API calls, same
  approach as 9a): empty/populated AI pane, tab switching, tab-reset-on-reselect,
  generate-form placement and visibility, no-forced-switch-while-generating,
  selected-row highlight (including after re-filtering and no-results states).
  No console errors observed at any step.

## Findings

No new findings from this feature. Pre-existing ledger entries (F-03/F-04/F-05,
P2, and F-07, P3, from 9a) remain open/untouched; F-06 (fixed in 9a) also
remains untouched. None are P0/P1, so none blocked this completion.

This feature was the last consumer of `prototypes/` (`library.html`); the
folder is discarded as part of this completion's commit.
