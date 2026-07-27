# Feature: Handle invalid/unreachable YouTube URLs gracefully

**From build-plan:** Phase 7: Polish & Edge Cases (item 1)
**Status:** complete

## Goal

Make sure a bad URL never produces a broken or silently wrong result. Investigation found the general case (malformed URL, 404, unavailable video, unreachable host, empty input) is already handled: `fetch_metadata`/`download_audio` catch `yt_dlp.utils.DownloadError`, the routes convert it to `HTTPException(400, ...)`, and the frontend already renders `body.detail` in the error banner without crashing. The real gap is playlist URLs: yt-dlp defaults to playlist mode whenever a URL carries a `list=` param (including a normal single-video URL copied while watching a playlist), so instead of raising an error it silently returns playlist-level info (wrong id, wrong title, `duration: None`) and would attempt to download the whole playlist into one video's folder.

## In scope

- `backend/youtube.py`: pass `noplaylist: True` in the yt-dlp opts for both
  `fetch_metadata` and `download_audio`, so a video URL with a trailing
  `list=` param resolves to just that video (verified this alone fixes the
  common case).
- Detect the remaining case, a bare playlist URL with no resolvable single
  video (`info.get("_type") == "playlist"`), and raise `YouTubeError` with a
  clear message instead of returning playlist metadata.
- Unit tests in `backend/test_youtube.py` covering both functions receiving a
  playlist-shaped result.

## Out of scope

- The general invalid/unreachable-URL path - already handled, already
  covered by existing tests (`test_download_audio_raises_youtube_error_on_download_error`,
  etc.). Not touching it.
- The metadata-preview/confirmation-banner UI described in
  project-overview.md - the frontend calls `/download` directly today and
  never calls `/metadata`. That's a pre-existing gap from Phase 1, not part
  of this fix; flagged as a note for a separate pass, not fixed here.
- Rate limiting, retries, or any other yt-dlp option beyond `noplaylist`.

## Build steps

- [x] **Step 1 - Reject playlist URLs** - add `noplaylist: True` to the
  `ydl_opts` in `fetch_metadata` and `download_audio`; after `extract_info`,
  raise `YouTubeError("This looks like a playlist. Paste a link to a single video instead.")`
  when `info.get("_type") == "playlist"`. Add tests to `backend/test_youtube.py`:
  a fake YDL playlist-shaped result raises `YouTubeError` from both
  `fetch_metadata` and `download_audio`; a video-with-`list=`-param case
  (mocked) still resolves normally. *Done when:* `pytest backend/test_youtube.py`
  passes with the new cases, and a manual check against a real playlist URL
  (`/api/videos/metadata`) returns 400 with the playlist message instead of
  200 with bogus metadata.

## Files / areas

- `backend/youtube.py`
- `backend/test_youtube.py`

## Data / contracts

None new - `YouTubeError` and the existing 400 `HTTPException` path already
carry the message through to the frontend's `body.detail` error banner.

## Testing

Test command: `pytest` (declared in `AGENTS.md`, so the test gate applies).
This step adds in-scope logic (playlist detection) and ships unit tests with
it. No UI changes, so no new browser verification beyond confirming an
existing manual/API check.

## Notes for the AI

- Keep the existing `YouTubeError` -> `HTTPException(400, ...)` path; don't
  add a new error type.
- Don't touch the frontend - it already surfaces `detail` from a 400
  response correctly for both `/metadata`... (unused today) and `/download`.

## Notes

Self-review during Step 1 caught a real bug in the first pass: checking
`info.get("_type") == "playlist"` *after* `extract_info(url, download=True)`
in `download_audio` was too late - manual verification against a real
playlist URL showed yt-dlp had already downloaded the first entry's full
audio (74MB) by the time `_type` was known, and `prepare_filename` on the
playlist-level info didn't even resolve to the file that was actually
written (`audio.NA` vs. the real `audio.webm`), so cleanup would have missed
it. Fixed by dropping that check entirely and relying on `fetch_metadata`'s
pre-check (the only call site, via `start_download`) as the actual
system boundary, per `coding-standards.md`'s "only validate at system
boundaries" - `noplaylist: True` alone still fixes the common case (a video
URL carrying a `list=` param). Verified end-to-end against the real yt-dlp
and a running server: bare playlist URL rejected with 400 before any
download starts (confirmed no folder/file created), and a video+list-param
URL downloads correctly as the single video.

Targeted audit (scope: this diff, `backend/youtube.py` +
`backend/test_youtube.py`) found no new P0-P3 issues. Pre-existing open
findings `F-03`/`F-04`/`F-05` in `blueprint/context/findings.md` are
unrelated to this change (routes/storage/frontend, not touched here) and
remain in the ledger.

## Findings

None raised or resolved by this feature.
