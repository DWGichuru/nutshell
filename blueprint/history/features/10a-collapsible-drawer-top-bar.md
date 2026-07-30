# Feature: Collapsible drawer + persistent top bar

**From build-plan:** feature 10a
**Status:** complete

## Goal

Add a persistent top bar above the drawer (wordmark + a hamburger icon), and
make the drawer collapsible: clicking the hamburger hides it fully so both
panes gain width, while the wordmark and hamburger stay accessible either way.
This reverses 9a's "drawer is persistent, not collapsible" decision, per the
plan update approved this session.

## Design reference

No mockup for this one - it's a small, mechanical UI addition (a bar + a
toggle) rather than a new visual system, and the existing palette/typography
already cover it. "Logo" here means the existing text wordmark treatment
("Nutshell" in `font-serif text-2xl font-bold text-terracotta`), just
relocated - wiring the actual `blueprint/assets/icon.svg`/`wordmark-*.svg`
files into the app is a separate, unrequested change and stays out of scope.

## In scope

- A persistent `<header>` top bar spanning the full width, above the
  drawer+content row, containing: a hamburger icon button and the "Nutshell"
  wordmark (moved out of the drawer). Always visible.
- The drawer becomes collapsible: clicking the hamburger fully hides it
  (`display: none`, not a slide/width animation) so the interaction pane and
  AI-generated pane expand to use the freed width; clicking again restores it.
- Works identically on both New Summary and Library, since the drawer is a
  single shared element, not page-specific - no page-specific logic needed.
- Basic accessibility: `aria-label` and `aria-expanded` on the hamburger
  button, reflecting the drawer's current state.
- Dark mode support on the new top bar and hamburger icon.

## Out of scope

- The draggable resize divider (10b) - separate sub-feature.
- Any slide-in/out animation or transition for the drawer - instant show/hide
  only, for now.
- A different icon or visual state change on the hamburger itself when the
  drawer is open vs. collapsed (only `aria-expanded` changes, not the icon).
- Wiring the actual `blueprint/assets/` SVG logo/wordmark files into the app -
  the existing text wordmark is what moves, unchanged.
- Persisting the collapsed/expanded state across reloads - resets to expanded
  on every page load, matching the "no persistence" default already set for
  10b's resize state.
- Any backend or API changes - frontend-only, same as 9a/9b.

## Build steps

- [x] **Step 1 - Top bar structure (no toggle behavior yet)** - Restructure the
      outer shell from a single `flex h-screen` row into a `flex h-screen
      flex-col` layout: a new `<header id="top-bar">` row (hamburger icon
      button + "Nutshell" wordmark, moved out of `<aside>`) above a second row
      containing the existing `<aside id="drawer">` (nav only now) and the
      content area, unchanged otherwise.
- [x] **Step 2 - Wire the collapse toggle** - Add a `toggleDrawer()` function
      in `app.js` that toggles the `hidden` class on `<aside id="drawer">` and
      updates the hamburger button's `aria-expanded` attribute; wire it to the
      hamburger button's click event.

## Files / areas

- `frontend/index.html` - top bar markup, hamburger button, `<aside>`
  restructure (wordmark removed, kept nav-only).
- `frontend/js/app.js` - `toggleDrawer()` and its click listener.

## Data / contracts

- None. No backend routes, request/response shapes, or stored data change.

## Testing

- No new pure logic - a single class/attribute toggle wired to a click event.
  Rode on browser evidence per the testing gate, not new pytest tests.
- `pytest`: 89 passed (no backend files touched).

## Completion evidence

- Playwright, light + dark mode, both pages: top bar renders full-width above
  the drawer+content row; hamburger click hides the drawer entirely and both
  panes expand to fill the freed width; `aria-expanded` flips `true`/`false`
  correctly; drawer stays collapsed across a page switch (verified by invoking
  the view-switch function directly, since the nav buttons live inside the
  drawer and are intentionally unreachable while it's collapsed - only the
  hamburger stays accessible, matching the approved design). No console errors
  at any step.
- Note: because the nav buttons (`#nav-new-summary`/`#nav-library`) live
  inside `<aside id="drawer">`, collapsing the drawer also hides page
  navigation - the hamburger is the only way back. This matches the spec's
  "wordmark and hamburger stay accessible either way" wording (nav isn't
  listed as staying accessible) and was confirmed intentional during
  implementation, not a defect.

## Findings

No new findings from this feature. Pre-existing ledger entries (F-03/F-04/F-05,
P2, and F-07, P3) remain open/untouched; F-06 (fixed) also remains untouched.
None are P0/P1, so none blocked this completion.
