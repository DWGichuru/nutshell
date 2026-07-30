# Feature: Draggable resize divider

**From build-plan:** feature 10b
**Status:** complete

## Goal

Make the boundary between the interaction pane and the AI-generated pane
draggable on both New Summary and Library, so the user can resize the two
columns to fit what they're doing (e.g. widen the transcript/summary reading
area, or the form). Completes Phase 10 alongside 10a's collapsible drawer.

## Design reference

No mockup - it's a single interaction pattern (a draggable divider) applied to
an existing layout, not a new visual system. The existing palette covers the
divider's resting/hover/active states.

## In scope

- A vertical divider element between `#interaction-pane` and `#ai-pane` on New
  Summary, and between `#library-interaction-pane` and `#library-ai-pane` on
  Library - each pane pair gets its own divider, matching how those panes are
  already page-specific (not shared) elements.
- Dragging the divider resizes the interaction pane's width live (in px);
  the AI-generated pane fills the remaining space via its existing `flex-1`.
- Sensible min/max clamping during a drag so neither pane can be resized to an
  unusable size: interaction pane min 280px, and a max that always leaves the
  AI-generated pane at least 320px, computed from the current container width
  (so the max isn't a stale fixed number if the window is a different size).
- Drag indicators on the divider: default resting style (thin, muted), a
  hover style, and a distinct active/dragging style (e.g. terracotta
  highlight) so it's visually obvious the boundary is interactive and when a
  drag is in progress. `cursor: col-resize` throughout.
- One shared resize function/module used by both pages' divider+pane pairs
  (not duplicated per page), since the behavior itself is identical and
  page-agnostic - only the target elements differ.
- Basic accessibility: `role="separator"` and `aria-orientation="vertical"`
  on each divider.
- Dark mode support on the divider's resting/hover/active states.

## Out of scope

- Persisting the resized width across reloads - resets to the default
  `420px` on every full page load, per the existing "no persistence"
  decision for this feature. (Within a session, switching between New
  Summary and Library preserves each page's own resized width rather than
  resetting on every switch - this matches the precedent 10a set for the
  drawer's collapsed state, chosen over a literal "reset on every switch"
  reading during implementation.)
- Keyboard-driven resizing (arrow keys on a focused divider) - mouse/pointer
  drag only for now.
- Touch/mobile drag support - this is a desktop-only tool (existing
  decision from 9b).
- Reactively re-clamping an already-set width when the browser window is
  resized afterward - clamping only happens during an active drag.
- Any change to the drawer or its collapse behavior - that's 10a, already
  shipped.
- Any backend or API changes - frontend-only, same as 9a/9b/10a.

## Build steps

- [x] **Step 1 - Divider + resize mechanism on New Summary** - Added
      `#pane-divider` between `#interaction-pane` and `#ai-pane`, dropping
      `interaction-pane`'s `border-r`. Added `makeResizablePane()` in
      `app.js` using pointerdown/pointermove/pointerup on `document`,
      clamped to `[minWidth, containerEl.offsetWidth - minRemainder -
      dividerWidth]`. Dragging state swaps `DIVIDER_RESTING_CLASSES` for
      `DIVIDER_DRAGGING_CLASSES` (add/remove pairs, not a single toggled
      class) to avoid the same-specificity class-fight bug found and fixed
      as F-06 in 10a. Wired for New Summary with `minWidth: 280,
      minRemainder: 320`.
- [x] **Step 2 - Apply to Library** - Added `#library-pane-divider` between
      `#library-interaction-pane` and `#library-ai-pane`, dropping that
      pane's `border-r`, and called the same `makeResizablePane()` with
      Library's elements and the same bounds.

## Files / areas

- `frontend/index.html` - divider markup on both New Summary and Library,
  `border-r` removed from both interaction panes.
- `frontend/js/app.js` - `makeResizablePane()`, `DIVIDER_RESTING_CLASSES`/
  `DIVIDER_DRAGGING_CLASSES`, and its two call sites.

## Data / contracts

- None. No backend routes, request/response shapes, or stored data change.

## Testing

- No JS test runner is configured for this project; rode on browser evidence
  per the testing gate, same treatment as 9a/9b/10a.
- `pytest`: 89 passed at every step (no backend files touched).

## Completion evidence

- Playwright, both pages, light + dark mode: dragging the divider resizes
  the interaction pane live and the AI pane reflows; dragging past either
  bound clamps (280px min; max leaves the AI pane exactly 320px); the
  divider swaps to a solid terracotta highlight while dragging and back to
  its resting style on release; `cursor: col-resize` over the divider.
  New Summary's width is unaffected by Library's resize (separate DOM
  elements, no leaked state). A full page reload resets Library's width
  back to 420px, confirming no persistence. No console errors at any point.

## Findings

No new findings from this feature. Pre-existing ledger entries (F-03/F-04/F-05,
P2, and F-07, P3) remain open/untouched; F-06 (fixed) also remains untouched.
None are P0/P1, so none blocked this completion.

This completes Phase 10 (10a + 10b).
