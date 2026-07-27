# YouTube Video Summarizer — Build Plan

Sequential checklist for building the app. Each phase builds on the previous one — complete and test a phase before moving to the next.

## Phase 0: Project Setup
- [x] Initialize project repo, create `.gitignore` (exclude `.env`, `data/`)
- [x] Set up Python virtual environment
- [x] Install core dependencies: `fastapi`, `uvicorn`, `yt-dlp`, `python-dotenv`
- [x] Confirm `ffmpeg` is installed on the system (via Homebrew)
- [x] Create base folder structure: `backend/`, `frontend/`, `data/videos/`
- [x] Create empty `.env` file with placeholder for API key(s)
- [x] Create minimal FastAPI app that runs and serves a "hello world" route

## Phase 1: YouTube Download
- [x] Build endpoint to accept a YouTube URL
- [x] Fetch video metadata (title, channel, duration) via `yt-dlp` without downloading
- [x] Implement duration check — return warning + estimated transcription time if over threshold (e.g. 60 min)
- [x] Implement audio download via `yt-dlp` (best audio track)
- [x] Convert downloaded audio to a consistent format via `ffmpeg` if needed
- [x] Generate `video_id` and create `data/videos/{video_id}/` folder
- [x] Save `audio.mp3` and `meta.json` (title, channel, duration, date added)
- [x] Test: download a short video and confirm folder/files are created correctly

## Phase 2: SQLite Index
- [x] Design schema: `videos` table (video_id, title, channel, duration, date_added, path)
- [x] Create `data/index.db` and initialization script
- [x] Write function to insert/update index row on new video download
- [x] Write function to rebuild the full index by scanning `data/videos/*/meta.json`
- [x] Test: download a couple of videos, confirm index rows match folder contents

## Phase 3: Waveform Trimming (Frontend)
- [x] Set up basic frontend page structure with Tailwind CDN included
- [x] Integrate wavesurfer.js, load and render waveform for downloaded audio
- [x] Implement draggable trim region (start/end handles)
- [x] Implement playback preview of the selected trim region
- [x] Build endpoint to accept trim start/end and produce a trimmed audio file via `ffmpeg`
- [x] Test: trim a sample audio file and confirm output matches selected range

## Phase 4: Transcription (Local + API)
- [x] 4a. API transcription path - adapter interface, OpenAI Whisper API adapter, endpoint, method-aware progress status, `transcript.json` save, method picker UI showing API as the working option
- [x] 4b. Local transcription path - `mlx-whisper` local adapter, enable Local in the method picker, local-specific progress handling, test comparing both methods' output and recorded method

## Phase 5: AI Summarization
- [x] Design adapter interface for summarization providers (e.g. `summarize(transcript, format, api_key)`)
- [x] Implement adapter for at least one provider (e.g. Anthropic)
- [x] Load API key from `.env` via `python-dotenv`
- [x] Build format picker in UI: paragraph / bullet points / chaptered
- [x] Build endpoint to generate summary given transcript + selected format
- [x] Save summary output to `data/videos/{video_id}/summaries/{timestamp}_{format}.md`
- [x] Test: generate all three formats for a sample transcript, confirm output quality and file saving

## Phase 6: Library View (Search/Filter)
- [x] Build endpoint to list all videos from the SQLite index
- [x] Build search/filter endpoint (by title/channel substring, date range)
- [x] Build frontend library view: list of past videos with title/channel/date
- [x] Add search/filter input UI, wired to the filter endpoint
- [x] Implement "select video" flow: load its `meta.json`, `transcript.json`, and past summaries
- [x] Allow generating a new summary format from the library view without re-downloading or re-transcribing
- [x] Test: search across multiple videos, confirm correct filtering and reload behavior

## Phase 7: Polish & Edge Cases
- [x] Handle invalid/unreachable YouTube URLs gracefully
- [x] Handle very short clips / silence (transcription edge cases)
- [ ] Add loading states/spinners for download, transcription, and summarization steps
- [ ] Confirm Tailwind styling is consistent across all views
- [ ] Add basic error messages/toasts for failed API calls (e.g. missing/invalid API key)
- [ ] Final end-to-end test: full flow from URL input to saved summary, then reload from library

## Phase 8 (Optional / Future)
- [ ] Support additional summarization providers beyond the first
- [ ] Add ability to delete a video and its data from the library
- [ ] Add export options (e.g. copy summary, download transcript as `.txt`)
- [ ] Add index rebuild trigger in the UI (manual "resync" button)
