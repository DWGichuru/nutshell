# Coding Standards

> Your conventions. Edit these once to match your stack. Tuned for this
> project's real stack: Python + FastAPI backend, React + TypeScript (Vite
> build) + Tailwind CSS frontend, SQLite via stdlib `sqlite3`. Single local
> user, no auth.

## Python

- Python 3.14 (via Homebrew `python@3.14`, used to create `venv/`)
- Type hints on function signatures (params and return type); avoid bare
  `Any` where a concrete type or `TypedDict`/dataclass is known
- Use `dataclasses` or `TypedDict` for structured shapes (e.g. transcript
  segments, adapter results) instead of passing raw dicts around untyped
- f-strings for formatting, `pathlib.Path` for filesystem paths

## FastAPI

- One `FastAPI()` app in `backend/main.py`; route modules under
  `backend/routes/` as the surface grows, included via `APIRouter`
- Pydantic models for request/response bodies - never accept or return raw
  untyped dicts across an API boundary
- Raise `HTTPException` with a real status code and message for expected
  failure cases (bad URL, missing video, transcription failure); let
  FastAPI's default handler produce 500s for truly unexpected errors
- Long-running work (download, transcription, summarization) runs as a
  background task or polled-status endpoint, not a blocking request - the
  frontend needs to show progress per the UI/UX spec
- Adapters (transcription, summarization) are plain Python modules/classes
  behind a shared interface, selected by a `method`/`provider` argument -
  not baked into route handlers

## File Organization

- Routes: `backend/routes/[feature].py`
- Adapters: `backend/adapters/transcription/[method].py`,
  `backend/adapters/summarization/[provider].py`
- Data access (SQLite index): `backend/db.py` or `backend/index.py`
- Video storage helpers (folder layout, `meta.json`, etc.): `backend/storage.py`
- Frontend: `frontend/src/pages/[Page]/` (page + its sections),
  `frontend/src/components/{layout,shared}/` (shared components),
  `frontend/src/hooks/use[Name].ts`, `frontend/src/lib/[name].ts` (pure
  logic), `frontend/src/api/` (typed client + shared types)
- Pydantic models / shared types: `backend/models.py` (or split per feature
  once it grows)

## Naming

- Python files/functions/variables: `snake_case`
- Python classes (Pydantic models, adapter classes): `PascalCase`
- Constants: `SCREAMING_SNAKE_CASE`
- TypeScript files/functions/variables: `camelCase` (`format.ts`,
  `usePolling.ts`); React components: `PascalCase` (`TopBar.tsx`)
- Video folder / `video_id`: derived from the YouTube video id, lowercase

## Styling

- Tailwind CSS v3 via PostCSS, configured in `frontend/tailwind.config.js`
- Use the palette and typography from `project-overview.md` (Design section)
  as Tailwind theme values
- No inline styles beyond what's unavoidable for wavesurfer.js mount points
- Light mode first, dark mode as option

## Database

- SQLite via stdlib `sqlite3`, no ORM
- Schema/migrations are plain `.sql` or inline `CREATE TABLE IF NOT EXISTS`
  statements run at startup - no migration framework for a single-table
  local index
- `index.db` is a derived cache: always rebuildable from `data/videos/*/meta.json`;
  never store data in it that doesn't also exist in a video's own folder

## Data Fetching

- Frontend calls the FastAPI JSON endpoints via `fetch()`; no server-rendered
  templates
- Validate all request bodies with Pydantic models on the way in
- Single local user - no per-user scoping needed, but never trust a
  client-supplied file path; always resolve video data through `video_id` ->
  `data/videos/{video_id}/`

## Error Handling

- Use try/except around external calls (`yt-dlp`, `ffmpeg`, transcription
  and summarization providers) and translate failures into a proper
  `HTTPException`
- API error responses follow `{"detail": "..."}` (FastAPI's default shape)
- Frontend shows user-friendly error messages/toasts on failed fetches;
  never surface raw stack traces in the UI

## Testing

The blueprint installs no test runner; testing is opt-in at the project level,
because the overlay can't know your stack. Adding unit testing is an explicit
setup task the AI can do through the normal workflow, either as a build-plan item
or with `/tests`. The setup should choose the stack-native runner, wire the
scripts or commands, add a small example test, and update the Commands section
of `AGENTS.md`.

When `AGENTS.md` declares a `Verify` command, treat it as the umbrella automated
gate. It combines only the checks this project actually has, in this order when
available: typecheck, tests, then build. The command does not enable an absent
test runner or replace focused evidence. It gives local work and optional CI one
exact command to run. `/ci` owns Verify and CI setup. `/tests` adds the real test
command to Verify when it already exists, but never creates CI only because
testing was configured.

**The opt-in switch is one signal: a `test` command in the Commands section of
`AGENTS.md`.** Declare one and **tests become a gate for logic-bearing steps**,
not an optional extra; leave it out and the loop verifies logic with the evidence
it already uses (run it, a screenshot, the build). Adding the runner is itself a
deliberate step, never a silent mid-step install. This is the single definition
of the switch; the skills and `ai-interaction.md` only point back here.

- **What to test (the scope rule):** pure logic where a wrong answer is possible -
  parsers, formatters, validators, id/slug builders, server actions. These have
  assertable inputs and outputs and real edge cases (empty, missing, malformed).
- **What not to test:** UI components and integration-level surfaces (render or
  export routes, anything driving a real browser or external service). Verify those
  with a screenshot and the build, not brittle unit tests.
- **The gate (when a runner is configured):** a build step that adds in-scope logic
  must ship a passing test in the same reviewable diff. The project's test command
  must be green before the step is approved, before any checkpoint commit, and
  before `/complete` merges. UI and integration-only steps are exempt and ride on
  screenshot plus build evidence.
- **When it's named:** the `/feature` spec's Testing section predicts the coverage,
  `/implement` writes the test with the step, and if a step surfaces logic the spec
  didn't foresee, add a focused test then.
- An empty suite should fail, not pass, so "no tests ran" never looks like "passed".
- Test files live next to source files (for example `feature.test.ts`).
- Run them via the project's test command (see Commands in `AGENTS.md`), not a
  hardcoded tool name.

Stack binding: this project uses pytest (`pytest` command, see `AGENTS.md`),
with monkeypatching or mocks for external dependencies (`yt-dlp`, `ffmpeg`
subprocess calls, transcription and summarization provider APIs). A root
`conftest.py` (empty) puts the repo root on `sys.path` so tests can import
`backend.*` modules directly.

## Browser Verification

For UI and integration behavior, prefer real browser evidence over reading the
code and assuming it works.

- If Playwright is already installed, or the Commands section of `AGENTS.md`
  declares a Playwright script, use Playwright for browser checks, screenshots,
  console-error checks, and user-flow verification.
- If Playwright is not installed, do not add it silently in the middle of an
  unrelated feature. Use the available dev server, browser screenshots, build
  output, API output, or manual verification evidence instead.
- Add Playwright only when the user asks for it, or when the current spec is
  explicitly about setting up browser automation.
- Browser evidence is especially important for flows that click, type, submit,
  navigate, download files, render complex layouts, or depend on client-side
  state.

## Code Quality

- No commented-out code unless specified
- No unused imports or variables
- Keep functions under 50 lines when possible

## Comments

Write code that explains itself; comment only what the code cannot say.
Over-commenting is a common AI tell, so resist it.

- Comment the **why**, not the **what**. Delete any comment that restates the code.
- No banner/header blocks, section dividers, or step-by-step narration of obvious
  code. A file does not need a comment announcing each region.
- A comment earns its place only when it captures something the code can't: a
  non-obvious decision, a gotcha or workaround, why a value is what it is, or a
  link to a spec or issue.
- Prefer self-documenting names and small functions over explanatory comments.
- Keep doc comments minimal: a one-line purpose on an exported type or function is
  plenty; don't write JSDoc that just repeats the signature.
- When in doubt, leave the comment out.

## Writing

- No em dashes (U+2014) in generated content: docs, comments, commit messages,
  READMEs, specs. They read as AI-generated.
- Use a hyphen for `term - description` separators; rephrase prose with commas,
  parentheses, or a colon. Avoid en dashes and the ellipsis character too.
