# Fix: Electron packaging - Step 1: env-var-driven data/ffmpeg/.env paths

**Type:** Fix

## Context

First of 5 steps from `blueprint/docs/electron-packaging-plan.md`'s "Suggested
build order," run individually per that doc's own recommendation. This step
does no Electron work - it only makes the backend's hardcoded paths
configurable via env vars, laying the groundwork so a later step (Electron's
main process) can point the backend at `userData` and a bundled `ffmpeg`
without touching this code again.

## The problem

`backend/storage.py`, `backend/db.py`, `backend/youtube.py`, and
`backend/main.py` currently hardcode paths relative to the process's working
directory (`data/videos`, `data/index.db`, `"ffmpeg"` on `PATH`,
`.env` in cwd, `frontend/dist`). Packaged as an Electron app, the working
directory and data location are controlled by Electron, not by a repo
checkout, so these need to become configurable.

## The fix

Added env-var overrides with backward-compatible defaults, per the plan's
"Required backend changes" table:

| File | Current | Change |
|---|---|---|
| `backend/storage.py` | `DATA_ROOT = Path("data/videos")` | Reads from `NUTSHELL_DATA_DIR` env var when set (module load time, via `_resolve_data_root()`), else keeps the current relative default |
| `backend/db.py` | `DB_PATH = Path("data/index.db")` | Same pattern, derived from the same `NUTSHELL_DATA_DIR` var (`<dir>/index.db`, via `_resolve_db_path()`) |
| `backend/youtube.py` | `"ffmpeg"` passed to `subprocess.run` (2 call sites: `trim_audio`, `convert_to_mp3`) | Added `ffmpeg_path()` helper reading `NUTSHELL_FFMPEG_PATH` when set, else falling back to `"ffmpeg"` on `PATH`; used at both call sites |
| `backend/main.py` | `load_dotenv()` (loads `.env` from cwd) | `load_dotenv(dotenv_path=os.environ.get("NUTSHELL_ENV_FILE"))` - `python-dotenv` already defaults to cwd `.env` when `dotenv_path` is `None` |
| `backend/main.py` | `FRONTEND_DIST_DIR = "frontend/dist"` | Reads from `NUTSHELL_FRONTEND_DIR` env var when set, else keeps the current relative default |

Existing dev workflow (`uvicorn backend.main:app --reload`, `pytest`) with no
env vars set is unaffected - every default stays exactly as it was.

## Build steps

- [x] 1. Add env-var overrides to `storage.py`, `db.py`, `youtube.py`,
      `main.py`, with unit tests for the new pure-logic pieces
      (`ffmpeg_path()` resolution with the env var set vs. unset; `DATA_ROOT` /
      `DB_PATH` derivation from `NUTSHELL_DATA_DIR` set vs. unset), following
      the existing test patterns (monkeypatching env vars, no real
      filesystem/network/ffmpeg calls).

## Verified

- `pytest` - 95 passed (6 new tests added), including `ffmpeg_path()` and
  `_resolve_data_root()`/`_resolve_db_path()` resolution.
- Booted `uvicorn backend.main:app` with no env vars set: `GET /` -> 200,
  `GET /api/videos` -> 200 against real existing library data - default
  behavior unchanged.
- Booted with `NUTSHELL_DATA_DIR=/tmp/nutshell-test-data` and
  `NUTSHELL_FFMPEG_PATH=/usr/local/bin/ffmpeg` set: confirmed `DATA_ROOT`,
  `DB_PATH`, and `ffmpeg_path()` all resolved to the overridden paths.

## Out of scope

Everything else in `blueprint/docs/electron-packaging-plan.md`: the
`electron/` project itself, bundling a Python runtime or `ffmpeg` binary, the
Settings UI for API keys, and Forge packaging. Each is a separate future
`/fix` per the plan's suggested build order.
