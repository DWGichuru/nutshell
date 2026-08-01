# Feature: React frontend rewrite - cutover + regression

**From build-plan:** feature 11e
**Status:** complete

## Goal

Retire the vanilla HTML/JS frontend now that the React + TypeScript rewrite
(11a-11d) has full behavioral parity plus the three closed gaps (metadata
preview, dark mode, wordmark/favicon). Make the React app's build output the
one the backend actually serves, delete the old frontend, update the docs
that still describe the old stack, and run a full regression pass to prove
nothing broke in the switch.

## In scope

- Delete `frontend/index.html` and `frontend/js/app.js` (the vanilla
  implementation), then rename `frontend-react/` to `frontend/` so the app
  lives at the path `AGENTS.md` already says it will ("will become `frontend/`
  at cutover").
- Point `backend/main.py`'s static serving at the built output
  (`frontend/dist`, produced by `npm run build`) instead of the old
  `frontend/index.html` + `/frontend`-mounted source tree.
- Update `AGENTS.md` (Commands section) and `coding-standards.md` (File
  Organization, Styling) so they describe the shipped React/Vite/Tailwind-v3
  stack and the `frontend/` path, not `frontend-react/` or the CDN setup.
- Update `project-overview.md`'s Open Questions note for Phase 11 so it no
  longer says the running code is still the vanilla frontend.
- Full regression pass: build the app, run the existing automated checks,
  then exercise New Summary and Library in a real browser against the
  backend-served build (not the Vite dev server) in both light and dark mode.

## Out of scope

- Any behavioral change to the React app itself - 11a-11d already delivered
  parity plus the three gaps; this feature only changes where the build lives
  and how it's served.
- Adding CI/GitHub Actions for the new build (`/ci` is a separate, explicit
  step per `AGENTS.md`).
- Fixing the open P2/P3 findings in `blueprint/context/findings.md` (F-03,
  F-04, F-05, F-07, F-08) - none are P0/P1, none block this feature or
  `/complete`.

## Build loop

Build one step at a time, never the whole feature at once.

1. Plan mode lays out the step before any code.
2. The AI implements just that step.
3. It shows the diff (not full files); you read it and understand it.
4. You approve, then choose whether to commit a checkpoint or roll straight on.
   Checkpoints are optional; `/complete` makes the real feature-level commit at the end.

Never accept a step you haven't read. If a diff is too big to review, the step was too big, so split it.

## Build steps

- [x] **Step 1 - Directory cutover + backend serves the built app** -
      `git rm -r frontend/` (removes the old `index.html` and `js/app.js`
      entirely, so the destination path is clear), then
      `git mv frontend-react frontend` so the whole Vite/React tree - source,
      `node_modules/`, and any existing `dist/` - moves as one filesystem
      rename. In the moved `frontend/package.json`, change `"name"` from
      `"frontend-react"` to `"frontend"`, then run `npm install` inside
      `frontend/` so `package-lock.json`'s name field stays in sync (no
      dependency version changes expected). In the same step, update
      `backend/main.py`: replace the `FRONTEND_DIR = "frontend"`
      mount-at-`/frontend` + `@app.get("/") -> FileResponse("frontend/index.html")`
      pair with a single `StaticFiles(directory="frontend/dist", html=True,
      check_dir=False)` mount at `/`, registered after
      `app.include_router(videos_router)` so `/api/videos/*` routes keep
      matching first; remove the now-unused `FileResponse` import.
      `check_dir=False` matters here because `frontend/dist` is a gitignored
      build artifact - without it, the app would refuse to even start on a
      fresh clone before the first `npm run build`. Doing the rename and the
      backend repoint together (rather than as two steps) avoids an
      in-between state where `backend/main.py` still points at paths the
      rename just changed out from under it. *Done when:* `frontend-react/`
      no longer exists; `frontend/` contains the Vite/React source (`src/`,
      `index.html`, `vite.config.ts`, etc.) with no leftover vanilla
      `index.html`/`js/`; `npm run build`/`npm test`/`npm run lint` all pass
      from inside `frontend/`; with `frontend/dist` built, running
      `uvicorn backend.main:app --reload` from the repo root serves the real
      app at `http://localhost:8000/` (not just an API) with all built
      assets (`/assets/*.js`, `/assets/*.css`, `/favicon.svg`) loading as
      200s; `pytest backend/test_main.py` passes unchanged (title still reads
      "Nutshell"); and `/api/videos/*` endpoints still respond correctly
      through that same running server. `npm run dev` on `:5173` (proxying
      `/api` to `:8000`) still works too, for ongoing frontend development.
- [x] **Step 2 - Update docs for the shipped stack** - In `AGENTS.md`'s
      Commands section, replace the "React + TypeScript frontend, in
      `frontend-react/` during the Phase 11 rewrite (will become `frontend/`
      at cutover)" framing with a plain description of `frontend/` as the
      shipped frontend, keeping the same command list (`npm install`,
      `npm run dev`, `npm run build`, `npm test`, `npm run lint`) and noting
      that `npm run build` must be run at least once before the backend can
      serve the UI (mirroring what Step 1 wired up). In
      `coding-standards.md`, update the top summary line and the File
      Organization section's frontend bullet to describe the real structure
      (`frontend/src/pages/`, `components/`, `hooks/`, `lib/`, `api/`) instead
      of the old `frontend/index.html` + `frontend/js/[feature].js` +
      `frontend/css/` layout, and update the Styling section's "Tailwind CSS
      via CDN script tag - no build step, no `tailwind.config.js`" line to
      reflect the real Tailwind v3 + PostCSS build now in place. In
      `project-overview.md`'s Open Questions, remove the sentence "Until this
      phase completes, the actual running code is still the vanilla HTML/JS
      frontend described in past history entries" from the Phase 11 bullet,
      since it no longer applies once this step ships. *Done when:* none of
      the three files mention `frontend-react/`, the CDN Tailwind setup, or
      the old `frontend/js/[feature].js` layout as current state.
- [x] **Step 3 - Full regression pass** - With `frontend/dist` freshly built
      and the backend running via `uvicorn backend.main:app` (no separate
      Vite dev server, so the browser only ever talks to `:8000`), exercise
      both flows against the existing stored videos in `data/videos/` (no
      live downloads, no paid transcription/summarization calls): Library
      search/filter/select and viewing an existing transcript + summary
      history, and New Summary's metadata-preview step against a URL already
      backed by local data. Repeat the pass in both light and dark mode
      (including the toggle itself and the wordmark swap), and check the
      browser console for errors throughout. *Done when:* every checked flow
      renders and behaves identically to the pre-cutover Vite-dev-server
      behavior documented in the 11a-11d history entries, in both themes,
      with a clean console, and the old vanilla frontend leaves no trace
      (`frontend/js/app.js` gone, `git status` shows no stray old-frontend
      files).

## Files / areas

- `frontend/` (renamed from `frontend-react/`) - `package.json` name field
  only content change; everything else moves as-is.
- `frontend/index.html`, `frontend/js/` (old vanilla frontend) - deleted.
- `backend/main.py` - static serving switched from the old source-tree mount
  to the built `frontend/dist` output.
- `AGENTS.md`, `blueprint/context/coding-standards.md`,
  `blueprint/context/project-overview.md` - docs updated for the shipped
  stack and path.
- No changes to any `frontend/src/**` application code - 11a-11d already
  built it.

## Data / contracts

- No new data shapes. Static serving contract changes: the backend now
  serves whatever is in `frontend/dist` at `/`, so `frontend/dist` must exist
  (via `npm run build`) before `uvicorn` can serve the UI - it did not need a
  build step before this feature.

## Testing

- No new pure logic in this feature - it's a file move, a static-serving
  wiring change, and doc edits, all UI/integration/infra rather than
  testable business logic, so it rides on build + existing-suite + browser
  evidence per `coding-standards.md`'s testing gate, not new unit tests.
- Run once per step as applicable, and again at the end: `npm run build`,
  `npm test`, `npm run lint` from `frontend/`; `pytest` from the repo root
  (covers `backend/test_main.py`, which must keep passing against the built
  `frontend/dist/index.html`).
- Step 3's manual/browser regression pass (Playwright, since it's already
  installed and used in 11a-11d) is the primary evidence this feature is
  correct - a rename and a static-mount swap are exactly the kind of change
  that can silently 404 an asset or break a relative path, and the existing
  test suites don't cover static-file serving end to end.

## Notes for the AI

- `frontend/dist` is gitignored (via `frontend/.gitignore`, inherited from
  the `frontend-react/.gitignore` in the rename) - it's a build artifact, not
  committed. That means a fresh clone needs `npm run build` run once before
  `uvicorn` can serve anything at `/`; `check_dir=False` on the `StaticFiles`
  mount keeps that a clear 404 instead of a startup crash, and Step 2 (docs)
  makes it a documented workflow step, not an oversight to work around.
- Register the `StaticFiles` mount in `backend/main.py` *after*
  `app.include_router(videos_router)`, matching how the old code already
  ordered its frontend mount after route registration - Starlette matches
  routes in registration order, so this keeps `/api/videos/*` resolving
  before the catch-all static mount ever sees those paths.
- `git rm -r frontend/` before `git mv frontend-react frontend` is required,
  not optional - `git mv` onto an existing directory nests the source inside
  it (`frontend/frontend-react/...`) instead of renaming, so the destination
  must be clear first. Use `git mv` for the actual rename (not delete +
  recreate) so history for the 11a-11d work stays attached to the moved
  files.
- Don't touch `frontend/README.md` (the Vite template boilerplate) - it's
  harmless and out of scope for this rename.
- The regression pass explicitly avoids live downloads or paid API calls,
  consistent with how 11a-11d were verified - reuse the videos already in
  `data/videos/` for both flows.

## Verification evidence

- `npm run build`, `npm test` (19/19), `npm run lint` - clean, from `frontend/`.
- `pytest` - 89/89 passing, including `backend/test_main.py` against the
  built `frontend/dist/index.html`.
- Manually confirmed `check_dir=False` behaves as intended: with
  `frontend/dist` temporarily moved aside, `uvicorn` still starts cleanly
  (no crash at import/startup) and only errors on an actual request to `/`;
  restoring `dist` and re-requesting worked immediately, no restart needed.
- Ran the real app via `uvicorn backend.main:app` (backend-served build only,
  no Vite dev server) and hit it directly: `/` returns the built `index.html`
  (200, `text/html`, contains "Nutshell"), `/favicon.svg` and both hashed
  `/assets/*.js` / `/assets/*.css` return 200, and `/api/videos` still
  responds 200 through the same server.
- Playwright regression against that same running server, using existing
  stored videos in `data/videos/` (no live downloads, no paid
  transcription/summarization calls): Library search/filter list renders,
  selecting a video (disambiguated by exact title/date, since two stored
  videos share a title prefix) shows its Transcript and Summary tabs with
  real content; New Summary's metadata-preview step made a real (free,
  non-download) `yt-dlp` lookup against a YouTube URL backed by local data
  and rendered title/channel/duration plus the long-video confirmation
  banner. Repeated the walkthrough after toggling dark mode (wordmark swap,
  toggle icon, panel colors) and confirmed the choice persists across a hard
  reload. Zero browser console errors and zero failed network requests
  (status >= 400) across the whole pass.
- `git status` after the pass shows no stray old-frontend files; `frontend/`
  is the only frontend directory on disk.
