# Feature: React frontend rewrite - dark mode toggle + wordmark/favicon assets

**From build-plan:** feature 11d
**Status:** complete

## Goal

Close the last two documented UI gaps from the React rewrite (11a-11c): wire
the already-present-but-dormant `dark:` Tailwind styling to a real, persisted
toggle, and replace the top bar's plain-text "Nutshell" heading and the
placeholder Vite favicon with the real `blueprint/assets/` wordmark and
favicon SVGs.

## Design reference

`blueprint/assets/wordmark-light.svg`, `blueprint/assets/wordmark-dark.svg`,
and `blueprint/assets/favicon.svg` are the reference and the source of the
assets used - not a mockup, the actual artwork to embed.

## In scope

- Dark mode toggle: a pure `resolveInitialTheme` decision function, a
  `useDarkMode` hook that applies/persists the theme and reads OS preference
  as the fallback, and a toggle button wired into `TopBar`.
- Wordmark: transparent-background copies of `wordmark-light.svg`/
  `wordmark-dark.svg`, swapped via Tailwind `dark:` visibility, replacing the
  current `<h1>Nutshell</h1>` text in `TopBar`.
- Favicon: the real `blueprint/assets/favicon.svg` copied over the Vite
  placeholder at `frontend-react/public/favicon.svg`.

## Out of scope

- `icon.svg` (the 512x512 app icon) - not referenced anywhere in the UI
  target per `project-overview.md` (only wordmark + favicon are applied).
- Backend serving cutover, deleting the old `frontend/` - 11e.
- Editing the `blueprint/assets/` source files themselves - only the copies
  used by the app are touched.
- Redesigning the top bar/drawer panel colors to exactly match the
  wordmark's original canvas color - handled by dropping the background rect
  from the copies instead (see Notes for the AI), not a palette change.

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight on.
   Checkpoints are optional; `/complete` makes the real feature-level commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the step was too big, so split it.

## Build steps

- [x] **Step 1 - Dark mode toggle** - Add `src/lib/theme.ts` exporting
      `resolveInitialTheme(stored: string | null, prefersDark: boolean):
      'light' | 'dark'` (pure) plus the `nutshell-theme` storage key
      constant; add `src/lib/theme.test.ts` covering stored `'dark'`, stored
      `'light'`, and no/invalid stored value falling back to
      `prefersDark`. Add `src/hooks/useDarkMode.ts`: a lazy `useState`
      initializer that calls `resolveInitialTheme` (reading
      `localStorage`/`matchMedia('(prefers-color-scheme: dark)')`) and
      synchronously applies the resulting class to `document.documentElement`
      before first paint, plus a `toggleTheme` that flips state, re-applies
      the class, and persists the new value to `localStorage`. Wire it into
      `App.tsx` and pass `theme`/`onToggleTheme` down to a new toggle button
      in `TopBar.tsx` (sun/moon inline SVG icons, matching the existing
      hamburger icon's style, `aria-label` reflecting the action). *Done
      when:* clicking the toggle flips every `dark:`-styled element on both
      pages immediately; reloading the page preserves the last explicit
      choice; clearing the stored preference and reloading matches the OS
      `prefers-color-scheme`; no console errors or flash of the wrong theme.
- [x] **Step 2 - Wordmark + favicon assets** - Copy
      `blueprint/assets/favicon.svg` to `frontend-react/public/favicon.svg`,
      overwriting the Vite placeholder (`index.html` already links
      `/favicon.svg`, no change needed there). Copy
      `blueprint/assets/wordmark-light.svg` and `wordmark-dark.svg` into
      `frontend-react/src/assets/`, each with its full-bleed background
      `<rect>` removed so the icon+text composite transparently. In
      `TopBar.tsx`, replace `<h1>Nutshell</h1>` with two `<img>` elements (the
      light variant `dark:hidden`, the dark variant `hidden dark:block`),
      fixed height, `alt="Nutshell"`. *Done when:* the browser tab shows the
      terracotta rounded-square favicon instead of the default Vite icon; the
      top bar shows the icon+wordmark image with no visible background-color
      seam against the top bar's own panel color, in both light and dark
      mode; toggling dark mode (Step 1's button) swaps the correct wordmark
      variant instantly.

## Files / areas

- `frontend-react/src/lib/theme.ts`, `theme.test.ts` - new.
- `frontend-react/src/hooks/useDarkMode.ts` - new.
- `frontend-react/src/App.tsx` - wires `useDarkMode`, passes `theme`/
  `onToggleTheme` to `TopBar`.
- `frontend-react/src/components/layout/TopBar.tsx` - toggle button,
  wordmark images, plain-text `<h1>` removed.
- `frontend-react/public/favicon.svg` - overwritten.
- `frontend-react/src/assets/wordmark-light.svg`, `wordmark-dark.svg` - new,
  transparent-background copies.
- No changes to `backend/`, the old `frontend/`, or any other
  `frontend-react/src/pages/` or `components/shared/` file.

## Data / contracts

- `localStorage` key `nutshell-theme`, value `'light' | 'dark'`.
- `resolveInitialTheme(stored: string | null, prefersDark: boolean): 'light'
  | 'dark'` - pure, the only tested unit in this feature.
- The `dark` class is applied to `document.documentElement` (not an inner
  wrapper), matching `tailwind.config.js`'s existing `darkMode: "class"` and
  keeping every `dark:` utility already written across 9-11c working
  unchanged.

## Testing

- `theme.test.ts` covers `resolveInitialTheme`'s branches: explicit stored
  `'dark'`, explicit stored `'light'`, and `null`/invalid stored value
  falling back to `prefersDark` (both `true` and `false`).
- No other new pure/branching logic - the hook's DOM/localStorage/matchMedia
  side effects and the `TopBar` markup changes are UI/integration, exempt
  per `coding-standards.md`'s testing gate; verify with the browser
  (toggle + reload persistence + favicon/wordmark rendering) instead of unit
  tests.
- Run `npm test`, `npm run build`, and `npm run lint` once at the end of this
  feature to confirm the suite (including the new `theme.test.ts`) and build
  stay clean. No backend changes, so `pytest` is unaffected.
- Manual verification runs against the dev server (`npm run dev`) in a real
  browser: toggle in both light and dark starting states, hard reload to
  confirm persistence, clear `localStorage` and reload to confirm OS-based
  fallback, and a visual check of the wordmark/favicon in both themes.

## Notes for the AI

- Apply the `dark` class to `document.documentElement`, not an inner div -
  this is what makes every existing `dark:` class already sprinkled through
  9-11c "just work" with zero changes to those files.
- Do the initial `classList` sync synchronously inside `useDarkMode`'s lazy
  `useState` initializer (runs during render, before paint), not in a
  `useEffect` - a deliberate, narrow exception to "no side effects during
  render", needed to avoid a flash of the wrong theme on load.
- Keep `theme.ts` limited to the pure decision function; `localStorage` reads/
  writes and the `matchMedia` query belong in the hook - same split already
  used for `lib/polling.ts` (pure) / `hooks/usePolling.ts` (wiring).
- The wordmark SVGs' background `<rect>` (`#F5F1EA` cream for light,
  `#1E1B16` near-black for dark) is a fixed full-bleed canvas, but the top
  bar's actual panel background is `bg-ivory dark:bg-espresso/60` - a
  different, close-but-not-identical color. Embedding the assets unedited
  would show a visible rectangle seam. Dropping just the background `<rect>`
  from the copies (icon mark + text stay pixel-identical) fixes this without
  touching the source files in `blueprint/assets/` or the app's color
  palette.
- `icon.svg` is not used anywhere in the UI target - don't wire it in.

## Verification evidence

- `npm run lint`, `npm run build` - clean in `frontend-react/`.
- `npm test` - 19/19 passing (3 new `theme.test.ts` cases covering
  `resolveInitialTheme`'s stored-valid, stored-invalid+system-dark, and
  stored-invalid+system-light branches).
- Playwright against the real running dev server + backend (real stored
  videos in `data/videos/`, no live downloads or paid API calls): clicking
  the toggle flips every `dark:`-styled element on both New Summary and
  Library pages instantly; the choice persists across a hard reload; with
  `localStorage` cleared and the OS color scheme emulated dark, the initial
  load matches OS preference; no console errors in any pass.
- Favicon: fetched `/favicon.svg` directly and confirmed it returns the real
  `blueprint/assets/favicon.svg` content (terracotta rounded square), not
  the Vite placeholder.
- Wordmark: screenshots in both light and dark mode confirm the icon+text
  image composites with no visible background-color seam against the top
  bar's `bg-ivory`/`dark:bg-espresso/60` panel, and swaps correctly with the
  toggle; also verified with the drawer collapsed (top bar stays correct
  when the drawer is hidden).
- Targeted audit of the diff (self-review, since no Playwright-detectable
  behavioral issue was found): matches spec, no scope creep, no new
  findings. `blueprint/context/findings.md` had no open or fixed P0/P1 at
  merge time (pre-existing F-03/04/05/07/08 are P2/P3 and untouched by this
  feature).
