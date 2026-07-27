# Findings

> **Generated file.** The findings ledger: review findings raised by `/audit`
> against the work in progress, each with a durable ID, severity (P0-P3), and
> status. `/implement` marks repaired findings `fixed`, a later `/audit` pass
> moves them to `closed`, and `/complete` refuses to merge while any P0 or P1
> finding is `open` or `fixed`, then archives resolved findings with the work
> and resets this file.

### F-03 [P2] open - Download, transcription, and summarization background tasks duplicate the same status-dict pattern

**File:** backend/routes/videos.py:50
**Found:** 2026-07-27 by /autopilot audit (scope: current)
**Why it matters:** `_download_status`/`_run_download`, `_transcription_status`/
`_run_transcription`, and `_summarization_status`/`_run_summarization` are
three near-identical copies of the same
pending -> running -> done/error in-memory status tracking pattern. This
feature's step added the third copy, following the existing (already
duplicated) convention rather than introducing new duplication on its own.
Three copies is past the usual "rule of three" threshold for extracting a
shared helper.
**Suggested fix:** Extract a small shared helper (e.g. a generic status-store
class or a `run_background_job(status_map, video_id, fn)` wrapper) used by all
three background tasks. Out of scope for this feature since it would also
touch the existing download and transcription code paths, not just the new
summarization code.
**Resolution:**

### F-04 [P2] open - `video_id` path segments are not validated against traversal before being joined into filesystem paths

**File:** backend/storage.py:16
**Found:** 2026-07-27 by /autopilot audit (scope: current)
**Why it matters:** `video_dir`, `audio_path`, `transcript_path`, and the new
`summaries_dir` all build paths as `DATA_ROOT / video_id / ...` without
validating `video_id`. A malicious `video_id` path segment (e.g. containing
`..`) could resolve outside `data/videos/`. This is a pre-existing,
project-wide pattern (present in `video_dir`/`audio_path`/`transcript_path`
before this feature) that `summaries_dir` extends rather than introduces.
Single-user local tool lowers real-world risk, but `coding-standards.md`
already calls out "never trust a client-supplied file path."
**Suggested fix:** Add a single `video_id` validation/sanitization helper in
`backend/storage.py` (e.g. reject any id containing `/`, `\`, or `..`) used by
every path-building function. Best done as one cross-cutting hardening pass
covering all existing endpoints, not scoped to this feature alone.
**Resolution:**
