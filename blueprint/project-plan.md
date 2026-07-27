# YouTube Video Summarizer — Project Plan

## Problem Statement
Watching or skimming a full YouTube video to extract its key information is slow. This project builds a local tool that takes a YouTube link, lets the user download and trim the relevant audio, transcribes it locally, and generates an AI-powered summary in a user-selected format — turning a long video into a fast, searchable, reusable text asset.

## Users
- Single user, running the app locally on their own machine (M4 Pro MacBook Pro, 24GB RAM).
- No multi-user support, authentication, or public deployment in scope.

## Core Features
1. **YouTube audio download** — paste a link, download the best available audio track via `yt-dlp`.
2. **Video length warning** — before downloading, check video duration and warn the user if it's long (e.g. over 60 minutes), with an estimated transcription time so they can decide whether to proceed.
3. **Waveform-based trimming** — visual waveform of the downloaded audio with drag handles to select a start/end range before transcription.
4. **Transcription (local or API)** — user chooses per run how the trimmed audio is transcribed:
   - **Local:** on-device via `mlx-whisper` (Metal-accelerated for Apple Silicon) — free, no internet dependency, slower for long clips
   - **API:** OpenAI's Whisper endpoint — faster and offloads compute, costs per minute of audio, requires the OpenAI API key from `.env`
   
   Both paths produce the same output shape: full transcript text plus segment-level timestamps.
5. **AI-generated summary** — transcript is sent to a user-configured AI provider (key stored in `.env`) to generate a summary. User selects the output format per run:
   - Plain paragraph summary
   - Bullet-point key takeaways
   - Timestamped/chaptered summary (uses segment timestamps)
6. **Per-video persistent storage** — every video's audio, transcript, and all generated summaries are stored together in one folder, so a single video's full history is self-contained.
7. **Past runs library with search/filter** — a browsable list of previously processed videos, backed by a SQLite index, filterable by title/channel/date, allowing the user to revisit past transcripts and summaries without reprocessing.

## Data Being Stored
Per video, grouped under `data/videos/{video_id}/`:
- `meta.json` — title, channel, duration, date added (source of truth for the video)
- `audio.mp3` — downloaded audio file
- `transcript.json` — full transcript text + segment-level timestamps + which transcription method was used (local/API)
- `summaries/{timestamp}_{format}.md` — one file per summary generation, so multiple summary runs/formats per video are all preserved

Additionally:
- `data/index.db` — SQLite index (video_id, title, channel, duration, date_added, path) derived from `meta.json` files, used purely for fast search/filter. Rebuildable at any time by re-scanning `data/videos/`.
- `.env` — stores the user's AI provider API key(s), excluded from version control via `.gitignore`.

## Tech Stack
- **Backend:** Python + FastAPI
- **Audio download:** yt-dlp
- **Audio processing:** ffmpeg (format conversion, trimming)
- **Transcription:** mlx-whisper (local, Metal-accelerated) or OpenAI Whisper API — user-selectable per run, sharing a common adapter interface
- **Summarization:** Adapter pattern supporting multiple AI providers (e.g. Anthropic, OpenAI), API key loaded from `.env` via `python-dotenv`
- **Index/search:** SQLite (Python stdlib `sqlite3`, no ORM)
- **Frontend:** HTML/JS, Tailwind CSS (via CDN, no build step), wavesurfer.js for waveform visualization/trimming
- **Deployment:** Local only — FastAPI dev server, accessed at `localhost`

## UI/UX Flow
1. **Home / New Summary view**
   - Input field for YouTube URL
   - On submit: fetch metadata, show title/channel/duration
   - If duration exceeds threshold, show warning banner with estimated processing time; user confirms to proceed
2. **Download & Trim view**
   - Audio downloads, waveform renders via wavesurfer.js
   - User drags trim handles to select start/end region, can preview playback of selection
   - "Transcribe" button proceeds with the trimmed selection
3. **Transcription & Summary view**
   - Transcription method picker: Local (mlx-whisper) or API (OpenAI Whisper) — API option shows a note about per-minute cost
   - Progress indicator during transcription (method-dependent: local shows on-device progress, API shows upload/processing status)
   - Once complete, transcript is displayed
   - Format picker (paragraph / bullets / chaptered) — user selects, triggers summary generation
   - Summary displayed alongside transcript; can regenerate with a different format without re-transcribing
4. **Library view**
   - Searchable/filterable list of past videos (by title, channel, date)
   - Selecting a video reloads its stored transcript and any past summaries, with the option to generate a new summary format without redownloading or re-transcribing

## Design Palette
Visual identity is built around the "Nutshell" mark (Style A — warm/organic walnut icon). Colors below are chosen to work as Tailwind custom theme colors.

| Role | Color | Hex | Usage |
|---|---|---|---|
| Primary / Brand | Terracotta | `#C96F45` | Icon fill, primary buttons, active states, links |
| Primary Dark | Burnt Terracotta | `#A85A38` | Button hover/pressed states, emphasis text on light backgrounds |
| Surface / Background | Cream | `#F5F1EA` | Main app background (light mode) |
| Card / Panel | Warm Ivory | `#F0E0C8` | Cards, panels, icon interior, waveform track background |
| Ink / Primary Text | Dark Espresso | `#3A2A1E` | Headings, primary body text |
| Muted Text | Warm Gray | `#8A7A6A` | Secondary text, captions, timestamps, placeholder text |
| Dark Surface | Near-Black Brown | `#1E1B16` | Dark mode background, wordmark-dark lockup background |
| Success / Confirm | Sage Green | `#3D5A3D` | Success states (e.g. transcription complete, saved) |
| Warning | Muted Rust | `#B5533C` | Duration warnings, error states, destructive actions |

**Typography pairing:** Georgia (or another serif) for the wordmark/headings to keep the organic, warm feel; a clean sans-serif (e.g. system default / Inter) for body text and UI controls to keep the interface readable and functional.

**Assets provided:**
- `assets/icon.svg` — standalone app icon mark (512×512, rounded square)
- `assets/favicon.svg` — simplified icon for small sizes (favicon/tab icon)
- `assets/wordmark-light.svg` — horizontal icon + name lockup for light backgrounds
- `assets/wordmark-dark.svg` — horizontal icon + name lockup for dark backgrounds
