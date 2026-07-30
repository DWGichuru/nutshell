# Fix: Adaptive summarization prompt

**Type:** Fix

## The problem

Nutshell's summarization prompt offered three flat, single-line instructions
selected via a `format` picker (`paragraph`, `bullets`, `chaptered`), each with
no shared structure and only `chaptered` using the transcript's timestamps.
Prompt-asset samples the user provided
(`blueprint/prompt-assets/sample-1.md`/`sample-2.md`/`sample-3.md`) showed a
richer structured template - Context, Opening, labeled main sections (each with
supporting evidence), Closing - that produces a more useful summary than any of
the three existing flat formats.

## The fix

Replace the three formats with one adaptive structured prompt, applied to
every summary, and remove the format concept end to end (backend types, API
request/response shape, storage filename scheme, frontend picker UI, and the
relevant `project-overview.md` spec text). Must not break: existing stored
summaries (including ones saved before this change, with the old
`{timestamp}_{format}.md` filename), the transcript/download/trim flow
(untouched), or the pytest suite.

## Build steps

- [x] **Adaptive prompt + drop format end to end** - New `SUMMARY_INSTRUCTION`
      in `backend/adapters/summarization/base.py` (Context -> Opening -> labeled,
      timestamped sections -> Closing), `build_prompt` always includes
      timestamps when segments exist. Dropped `format` from
      `SummarizeRequest`/`SummaryEntryModel` (`backend/models.py`),
      `SummaryEntry`/`write_summary`/`list_summaries` (`backend/storage.py`,
      filenames now `summaries/{timestamp}.md`), `_run_summarization`/
      `start_summarization`/`get_summaries` (`backend/routes/videos.py`), both
      provider adapters (`anthropic_api.py`, `openai_api.py`), and the format
      picker fieldsets + heading label in `frontend/index.html`/`app.js`.
      Updated `blueprint/context/project-overview.md` (Features, data model,
      UI/UX sections). *Done when:* `pytest` passes with tests updated to
      match (no `format` parametrization), and a real summarization run
      produces the new Context/Opening/labeled-sections-with-timestamps/
      Closing structure.

## Verify

- `pytest` - 86 passed.
- Confirmed a pre-existing legacy summary file (old `{timestamp}_paragraph.md`
  naming) still lists via `GET /api/videos/{id}/summaries` without error.
- Ran a real summarization (OpenAI provider) against a short existing test
  transcript; first pass surfaced doubled `### ##` headers (the instruction
  hardcoded a literal `##` level under an already-nested section), fixed the
  instruction to specify only the `[MM:SS]` prefix, reran and confirmed clean
  single-level headings and the intended four-part structure.
- Playwright screenshots of New Summary and Library detail views confirm no
  orphaned format picker and no layout breakage.
- Test-generated summary files and temporary `.env`/`data` symlinks (used to
  reuse local dev data for manual verification) were removed afterward -
  `git status` shows only the intended 13 source files changed.
