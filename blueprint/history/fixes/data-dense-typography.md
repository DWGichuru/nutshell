# Fix: Data-dense typography (font family + font scale)

**Type:** Fix

## The problem

The React frontend never actually loaded a custom webfont - `font-sans` and
`font-serif` both resolved to Tailwind's default stacks (`system-ui` and
Georgia respectively), so the app rendered in whatever sans font the OS
provided, not the "Inter" `coding-standards.md` already claimed for body text.
On top of that, every section heading used `font-serif text-xl` (a 20px
Georgia-style serif) and most controls (buttons, inputs, list items) had no
explicit text size, so they inherited the 16px base - noticeably larger and
more editorial than a data-rich tool calls for. Reviewed against
[ui.shadcn.com](https://ui.shadcn.com/) as a reference: shadcn uses a single
sans-serif typeface everywhere (headings included, differentiated by weight/
tracking, never by typeface) and a dense scale where most UI chrome sits at
`text-sm`/`text-xs`, reserving the 16px base for little beyond page body copy.

Confirmed with the user before writing this spec:

- Drop serif entirely - no `font-serif` anywhere in the app. (The "Nutshell"
  wordmark in `TopBar.tsx` is a separate SVG image asset, not CSS-styled
  text, so it's unaffected either way and out of scope here.)
- Self-host Inter as the one sans-serif typeface, everywhere - no CDN/Google
  Fonts network call at runtime.
- Adopt shadcn's dense scale: `text-sm` for controls (buttons, inputs,
  labels, drawer nav, list rows), `text-xs` for secondary/meta text (dates,
  durations, channel names, summary timestamps), `text-lg`/`text-xl` +
  `font-semibold tracking-tight` for headings instead of 20px serif.
  Transcript/summary reading content in `AiPane.tsx` and `LibraryAiPane.tsx`
  was already `text-sm` - correctly sized already, no change needed there.

## The fix

**Webfont + Tailwind config**

- Added `@fontsource-variable/inter` (self-hosted variable-weight Inter, no
  runtime network request) as a `frontend` dependency.
- Imported it once in `frontend/src/main.tsx`:
  `import '@fontsource-variable/inter';`
- In `frontend/tailwind.config.js`, set
  `theme.extend.fontFamily.sans = ['Inter Variable', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif']`
  (the package registers the family name as `'Inter Variable'` with a space -
  confirmed by reading the package's generated CSS during implementation,
  correcting this spec's original `InterVariable` guess). Kept a plain
  `Inter`/system fallback for the moment before the font file finishes
  loading. Left the `serif` key alone - Tailwind's default stays defined but
  nothing in the app references `font-serif` anymore after this fix.

**Drop serif, retarget headings**

Removed `font-serif` and resized six identical section-label headings
(previously `font-serif text-xl font-semibold`) to `text-lg font-semibold
tracking-tight`:

- `frontend/src/pages/NewSummaryPage/DownloadSection.tsx` ("New Summary")
- `frontend/src/pages/NewSummaryPage/TrimSection.tsx` ("Trim")
- `frontend/src/pages/NewSummaryPage/TranscribeSection.tsx` ("Transcribe")
- `frontend/src/pages/NewSummaryPage/SummarizeSection.tsx` ("Summarize")
- `frontend/src/pages/LibraryPage/SearchSection.tsx` ("Library")
- `frontend/src/pages/LibraryPage/GenerateSummarySection.tsx` ("Generate
  new summary")

`frontend/src/pages/LibraryPage/LibraryAiPane.tsx` (the selected video's
title, dynamic content rather than a fixed section label) dropped
`font-serif` and gained `tracking-tight` but kept `text-xl` - it reads as a
document/page title, not a form-section label.

**Retuned control and meta text sizes to the dense scale**

Added `text-sm` (previously unset, inheriting 16px) to:

- All primary action buttons: New Summary's Preview/Download, Summarize,
  Transcribe, Generate summary, Library's Filter, and the four trim-control
  buttons (skip back/play-pause/skip forward/Preview/Trim) in
  `TrimSection.tsx`.
- Text inputs: the URL input, and Library's search + date-from/date-to
  inputs.
- Drawer nav links (New Summary / Library).
- Library list rows: the video title span.

Shrunk to `text-xs` (previously `text-sm` or unset, used for secondary/meta
text - dates, durations, channel names, timestamps):

- The metadata preview channel/duration line.
- The channel/date subtitle under each Library list row.
- The channel/date line under the selected video's title.
- The per-summary timestamp.
- The trim section's Start/End time readout row.

Left everything else as-is: labels were already `text-sm font-medium`
(matched target), `Tabs.tsx` tab buttons were already `text-sm font-semibold`,
`AsyncStatus.tsx` status/error text stayed `text-sm` (it's an active status
message, not passive meta text), and the transcript/summary `<pre>` blocks
stayed `text-sm` per the confirmation above.

**Docs**

Updated the Typography line in `blueprint/context/project-overview.md`'s
Design section to describe the shipped result: Inter (self-hosted) everywhere,
dense `text-sm`/`text-xs` scale for controls and meta text, `text-lg`/`text-xl`
`font-semibold tracking-tight` for headings; noted the wordmark stays a
separate SVG asset outside this type scale.

## Build steps

- [x] **Step 1 - Load Inter, drop serif, resize headings**
- [x] **Step 2 - Retune control and meta text sizes**
- [x] **Step 3 - Update project-overview.md typography line**

## Files / areas

- `frontend/package.json`, `frontend/package-lock.json` - new
  `@fontsource-variable/inter` dependency.
- `frontend/src/main.tsx` - font import.
- `frontend/tailwind.config.js` - `fontFamily.sans` override.
- `frontend/src/pages/NewSummaryPage/{DownloadSection,TrimSection,TranscribeSection,SummarizeSection}.tsx`
- `frontend/src/pages/LibraryPage/{SearchSection,GenerateSummarySection,LibraryAiPane}.tsx`
- `frontend/src/components/layout/Drawer.tsx`
- `blueprint/context/project-overview.md` - Design/Typography line.

## Data / contracts

None - purely presentational (font family + Tailwind size utility classes).
No API, data model, or component prop changes.

## Testing

No new pure logic - this was a font/dependency addition plus Tailwind
className changes across existing components, which is UI/presentational
per `coding-standards.md`'s testing scope rule. The existing Vitest suite
stayed green with no assertion changes needed; verification rode on
`npm run build` + `npm run lint` + a browser pass in both light and dark
mode, not new unit tests.

## Verify

- `npm run build`, `npm test` (19/19), `npm run lint` from `frontend/` - all
  passed.
- `pytest` from the repo root - 89/89 passed, unchanged (no backend touched).
- Playwright pass against the built app (served via `uvicorn`, no Vite dev
  server) across New Summary and Library, both themes, including selecting a
  real stored video and viewing its Transcript tab: `getComputedStyle` on
  `<body>` and headings resolved to `"Inter Variable", Inter, ui-sans-serif,
  system-ui, sans-serif`; zero `font-serif` remained (`grep` confirmed and
  visually verified); zero browser console errors; no wrapping/overflow
  regressions in the video list, trim controls, or metadata preview card.
  The "Nutshell" wordmark (a separate SVG asset) was confirmed unaffected, as
  scoped.
