# Nutshell - Project Overview

> A local tool that turns a YouTube video into a trimmed, transcribed, AI-summarized text asset - paste a link, get a searchable summary.

## Problem

Watching or skimming a full YouTube video to extract its key information is
slow. Nutshell downloads the audio, lets the user trim it to the relevant
range, transcribes it locally or via API, and generates an AI summary in a
chosen format - turning a long video into a fast, reusable text asset.

## Users

- Single user, running the app locally on their own machine (M4 Pro MacBook
  Pro, 24GB RAM).
- No multi-user support, authentication, or public deployment in scope.

## Features

Build order below follows `build-plan.md` Phases 1-6 (the MVP loop). Phase 7 is
cross-cutting hardening applied after the loop works end to end, Phase 8 is
explicitly optional/future, Phase 9 is the 3-pane home page redesign (complete),
and Phase 10 adds the collapsible drawer/top bar and resizable pane divider on
top of that shell - see Open questions.

1. **YouTube audio download** - paste a link, fetch metadata (title/channel/duration),
   warn on long videos with an estimated transcription time, then download the
   best audio track via `yt-dlp` into a per-video folder. Headline feature - the
   entry point for every other feature.
2. **SQLite index** - a `videos` table derived from each `meta.json`, giving fast
   search/filter over past runs without scanning the filesystem. Rebuildable at
   any time.
3. **Waveform trimming** - render the downloaded audio as a waveform
   (wavesurfer.js), let the user drag start/end handles and preview the
   selection, then produce a trimmed audio file via `ffmpeg`.
4. **Transcription (local or API)** - a common adapter interface produces
   `{text, segments}` from either on-device `mlx-whisper` or the OpenAI Whisper
   API, user-selectable per run, with a method-aware progress indicator.
5. **AI summarization** - send the transcript to a configured AI provider and
   generate a summary in a user-picked format (paragraph, bullets, or
   timestamped/chaptered), saved alongside the transcript.
6. **Library view (search/filter)** - browse past videos by title/channel/date,
   reload a video's stored transcript and summaries, and generate new summary
   formats without re-downloading or re-transcribing.

## Data model

Per video, stored under `data/videos/{video_id}/`:

### meta.json (per-video metadata, source of truth for the video)

- `video_id` (string) - derived id, also the folder name
- `title` (string)
- `channel` (string)
- `duration_seconds` (int)
- `date_added` (ISO 8601 string)
- `source_url` (string) - original YouTube URL

### audio.mp3

- The downloaded (and, once trimmed, replaced/derived) audio file for the video.

### transcript.json

- `text` (string) - full transcript
- `segments` (array of `{start: float, end: float, text: string}`) - timestamped
  segments
- `method` (enum: `"local"` | `"api"`) - which transcription adapter produced
  this result

### summaries/{timestamp}\_{format}.md

- One file per summary generation; `format` is one of `paragraph`, `bullets`,
  `chaptered`. Multiple summary runs per video are all preserved, never
  overwritten.

### index.db (`videos` table, at `data/index.db`)

- `video_id` (text, primary key)
- `title` (text)
- `channel` (text)
- `duration_seconds` (int)
- `date_added` (text)
- `path` (text) - folder path for the video

> Rebuildable at any time by re-scanning `data/videos/*/meta.json`; it is a
> derived index, not a source of truth.

### .env (not a data model, but load-bearing)

- AI provider API key(s) (e.g. `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`), excluded
  from version control.

## Tech stack

- **Backend** - Python + FastAPI, serving both the API and the frontend.
- **Audio download** - `yt-dlp` for metadata fetch and best-audio-track download.
- **Audio processing** - `ffmpeg` for format conversion and trimming.
- **Transcription** - `mlx-whisper` (local, Metal-accelerated) or OpenAI Whisper
  API, behind a shared adapter interface, user-selectable per run.
- **Summarization** - adapter pattern over AI providers (e.g. Anthropic,
  OpenAI); API key loaded via `python-dotenv`.
- **Index/search** - SQLite via Python's stdlib `sqlite3`, no ORM.
- **Frontend** - HTML/JS + Tailwind CSS via CDN (no build step) +
  wavesurfer.js for waveform visualization/trimming.
- **Deployment** - local only, FastAPI dev server (`uvicorn`) at `localhost`.

## Monetization

Not in v1 - single-user local tool, no billing or accounts.

## UI/UX

Single 3-pane shell, no client-side router (vanilla HTML/JS):

- **Top bar (persistent, above the drawer)** - app logo/wordmark, title, and a
  hamburger icon that toggles the drawer. Always visible regardless of
  whether the drawer is open or collapsed.
- **Drawer (left, collapsible)** - navigation between New Summary and Library.
  Toggled via the top bar's hamburger icon; collapsing hides it fully so both
  panes gain width.
- **User-interaction pane (center)** - forms and actions for the active page:
  - New Summary: URL input; on submit, fetches and shows title/channel/duration,
    with a warning banner and required confirmation if duration exceeds the
    threshold (default 60 min); then sequentially reveals waveform trim
    controls (drag handles, preview playback), transcription method picker
    (Local vs API, with a cost note for API, method-aware progress indicator),
    and summary format picker (paragraph/bullets/chaptered) as each prior step
    completes.
  - Library: searchable/filterable list of past videos (title/channel/date);
    selecting one populates the AI-generated pane and offers generating a new
    summary format in place, without re-downloading or re-transcribing.
- **Resizable divider** - the boundary between the user-interaction pane and
  the AI-generated pane is draggable, with drag indicators, to resize both
  columns. Same behavior on both pages; sensible min-widths keep either pane
  from collapsing to unusable size. Resets on reload, not persisted.
- **AI-generated pane (right, tabbed)** - shows generated content for the
  active video: a Transcript tab and a Summary tab (reflecting the
  currently-selected/most recent format). Selecting a video from the Library
  page populates this pane the same way a fresh New Summary run does, so both
  pages share one content surface.

### Design

Palette (Tailwind custom theme colors), light mode first, dark mode as option:

| Role | Color | Hex |
|---|---|---|
| Primary / Brand | Terracotta | `#C96F45` |
| Primary Dark | Burnt Terracotta | `#A85A38` |
| Surface / Background | Cream | `#F5F1EA` |
| Card / Panel | Warm Ivory | `#F0E0C8` |
| Ink / Primary Text | Dark Espresso | `#3A2A1E` |
| Muted Text | Warm Gray | `#8A7A6A` |
| Dark Surface | Near-Black Brown | `#1E1B16` |
| Success / Confirm | Sage Green | `#3D5A3D` |
| Warning | Muted Rust | `#B5533C` |

Typography: serif (Georgia or similar) for wordmark/headings, system
sans-serif/Inter for body and controls. Icon/wordmark assets live in
`blueprint/assets/` (`icon.svg`, `favicon.svg`, `wordmark-light.svg`,
`wordmark-dark.svg`).

## Deployment

Local only - no host, no public deployment.

- **Run:** FastAPI dev server via `uvicorn`, accessed at `localhost`.
- **Env vars:** AI provider API key(s) in `.env` (excluded from version
  control); no other secrets.
- **Storage:** local filesystem (`data/videos/`) + local SQLite file
  (`data/index.db`); both excluded from version control.
- **No database server, no workers/cron, no health checks, no domain.**

## Open questions

- `build-plan.md` Phase 0 (project/environment setup: repo init, venv, core
  deps, folder structure, hello-world FastAPI app) is pre-build scaffolding,
  not a feature - it isn't reflected in Features above and shouldn't be spec'd
  through `/feature`. It's being done directly as initial scaffolding per this
  request.
- `build-plan.md` Phase 8 (additional summarization providers, delete-video,
  export options, manual index resync) is explicitly optional/future; treat it
  as a post-MVP backlog, not part of the Phase 1-6 build order above.
- `build-plan.md` Phase 9 (3-pane home page redesign: persistent drawer,
  user-interaction pane, tabbed AI-generated pane, with Library unified into
  the same shell) supersedes the "four views" layout described in earlier UI/UX
  drafts. It was split into sub-features (9a shell/New Summary, 9b Library
  unification) and is now complete.
- `build-plan.md` Phase 10 (resizable interaction/AI-pane divider with drag
  indicators; collapsible drawer via a hamburger icon, with logo/title/hamburger
  moved into a persistent top bar above the drawer) reverses Phase 9's "drawer
  is persistent, not collapsible" decision and adds a new top bar not present
  in the original 3-pane design. Applies identically to both the New Summary
  and Library pages, since they already share the same shell built in 9a/9b.
