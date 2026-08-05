# Electron Packaging Plan

> Reference document, not a Blueprint spec. It is not tracked in `build-plan.md`
> or `project-overview.md` (by request) - route the actual implementation
> through `/fix` or `/feature` steps manually when you're ready to build it.

## Goal

Turn Nutshell from "clone the repo, run two dev servers" into a double-clickable
macOS app: one `.dmg`/`.zip` that bundles the React frontend, the Python/FastAPI
backend, and their native dependencies (Python runtime, `ffmpeg`), so it runs
with no `venv`, `pip install`, or `npm install` on the target machine.

## Locked-in decisions

| Decision | Choice | Why |
|---|---|---|
| Platform scope | macOS only (Apple Silicon) | Matches the actual machine (M4 Pro, per `project-overview.md`); keeps `mlx-whisper` local transcription working everywhere the app runs |
| Python bundling | Embedded standalone Python runtime + populated venv, spawned directly | More reliable than freezing for a stack with native/dynamic loading (`mlx`, Metal kernels) than PyInstaller |
| Code signing / notarization | Skip for v1, ship ad-hoc/unsigned | Free; single-user local tool; you bypass Gatekeeper once via right-click > Open |
| Auto-update | Skip for v1 | Single-user tool, you control rebuild/reinstall; auto-update effectively requires signing anyway |
| `ffmpeg` | Bundle a static macOS arm64 binary as an app resource | Zero-setup install even if the target machine has no `ffmpeg` on `PATH` |
| Build tooling | Electron Forge | Electron's own docs now recommend Forge over rolling manual `electron-packager`/`electron-builder` config |

These are v1 defaults for a personal tool. Revisit signing and auto-update if
you ever hand this app to someone else.

## Target architecture

```
Electron app (.app bundle)
├── main process (Node, TypeScript)
│   - creates the BrowserWindow
│   - resolves userData dir, bundled resource paths
│   - picks a free localhost port
│   - spawns the bundled Python runtime running uvicorn
│   - health-checks it, then loads http://127.0.0.1:<port>/ in the window
│   - kills the backend child process on quit
│
├── renderer (BrowserWindow)
│   - loads the *already-built* React app over plain HTTP, same as today
│   - no code changes needed here: it's still same-origin fetches to /api/*
│
└── resources/ (bundled, not source-controlled)
    ├── python-runtime/          (relocatable CPython + installed deps)
    ├── bin/ffmpeg                (static macOS arm64 binary)
    ├── backend/                  (this repo's backend/ source, unfrozen)
    └── frontend-dist/            (this repo's frontend/dist build output)
```

The backend keeps being "FastAPI serves the API and the built frontend" - that
part of the architecture doesn't change. Electron just becomes the process that
starts that server locally and points a native window at it, instead of you
running `uvicorn` by hand and opening a browser tab.

Because the renderer loads real `http://` content (not `file://`), Electron's
default security posture (`contextIsolation: true`, `nodeIntegration: false`,
sandboxed renderer) already applies cleanly with no preload/`contextBridge`
work needed - the frontend doesn't talk to Electron APIs at all, only to its
own `/api/*` backend, exactly like it does today in the browser.

## Required backend changes

The backend currently hardcodes paths relative to the process's working
directory. Packaged, Electron controls the working directory and the data
location, so these need to become configurable (env vars, sensible dev-mode
defaults so `pytest` and `uvicorn --reload` keep working unchanged):

| File | Current | Change |
|---|---|---|
| `backend/storage.py` | `DATA_ROOT = Path("data/videos")` | Read from `NUTSHELL_DATA_DIR` env var when set, else keep today's relative default |
| `backend/db.py` | `DB_PATH = Path("data/index.db")` | Same pattern, derived from the same env var |
| `backend/youtube.py` | `"ffmpeg"` passed to `subprocess.run` (PATH lookup, 2 call sites) | Small helper (`ffmpeg_path()`) that reads `NUTSHELL_FFMPEG_PATH` when set, else falls back to `"ffmpeg"` on `PATH` |
| `backend/main.py` | `load_dotenv()` (loads `.env` from cwd) | `load_dotenv(dotenv_path=os.getenv("NUTSHELL_ENV_FILE"))`, still defaults to cwd `.env` when unset |
| `backend/main.py` | `FRONTEND_DIST_DIR = "frontend/dist"` | Same env-var-driven base-path pattern, or rely on Electron setting the child process's `cwd` to the resource directory that contains both `backend/` and `frontend/dist/` (simpler, no code change) |

All of these are additive, backward-compatible defaults - the existing
`AGENTS.md` dev workflow (`uvicorn backend.main:app --reload`, `pytest`) keeps
working exactly as-is with no env vars set.

**API keys.** Right now `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` come from a
hand-edited `.env` file in the repo root - fine for local dev, not something to
ask a packaged app's user to do. Add a minimal Settings view (new frontend
section + a small backend endpoint) that writes those two keys into a `.env`
file under Electron's `userData` directory, pointed at via `NUTSHELL_ENV_FILE`.
Plain file is consistent with how the project already treats this file (local,
gitignored, single-user); Electron's `safeStorage` (OS-keychain-backed
encryption) is a reasonable upgrade later if this ever leaves your machine.

## Data location

Move from the repo-relative `data/` folder to Electron's per-OS user data
directory: `app.getPath('userData')`, e.g.
`~/Library/Application Support/Nutshell/`. First-launch behavior: if `data/`
still exists at the old repo-relative path from prior dev usage, this plan
does **not** propose auto-migrating it - flag it in a first-launch check and
let you decide (dev data vs. real data) when you get there, since only you run
this today.

Leave the Hugging Face model cache (`~/.cache/huggingface`, where
`mlx-whisper` downloads model weights on first use) at its default OS-level
location rather than redirecting it into `userData`. It's already outside the
app bundle, persists across reinstalls/updates, and there's no reason to
duplicate model downloads per-app.

## Electron project structure

New top-level `electron/` directory:

```
electron/
├── package.json          (Forge config, main entry point)
├── forge.config.ts
├── src/
│   ├── main.ts            (app lifecycle, window, backend spawn/health-check/kill)
│   └── backend-sidecar.ts (resolve resource paths, spawn, port selection)
└── resources/              (gitignored - populated by the build script below)
    ├── python-runtime/
    └── bin/ffmpeg
```

Build-time script (`electron/scripts/build-python-runtime.sh` or similar):

1. Fetch a relocatable macOS arm64 CPython build (e.g. `python-build-standalone`,
   the same family of builds `uv` uses).
2. Install `requirements.txt` into that interpreter's `site-packages`.
3. Download a static macOS arm64 `ffmpeg` binary into `electron/resources/bin/`.
4. Copy `backend/` and a freshly-built `frontend/dist/` into
   `electron/resources/`.

Forge's `packagerConfig.extraResource` then copies `electron/resources/*` into
the app bundle's `Contents/Resources/`, readable at runtime via
`process.resourcesPath`.

## Runtime flow (packaged app)

1. `app.whenReady()` - Electron acquires a single-instance lock
   (`app.requestSingleInstanceLock()`) so a second launch focuses the existing
   window instead of spawning a second backend against the same data dir.
2. Resolve `userData` dir, `process.resourcesPath`, and a free local TCP port.
3. Spawn `resources/python-runtime/bin/python3 -m uvicorn backend.main:app
   --host 127.0.0.1 --port <port>` via `child_process.spawn`, with `cwd` set to
   `resources/` and `NUTSHELL_DATA_DIR` / `NUTSHELL_FFMPEG_PATH` /
   `NUTSHELL_ENV_FILE` set from step 2.
4. Poll a lightweight health endpoint (reuse `GET /` or add `GET /api/health`)
   until it responds; show a minimal loading state in the window in the
   meantime rather than a blank screen.
5. Load `http://127.0.0.1:<port>/` in the `BrowserWindow`.
6. On `before-quit` / `window-all-closed`, send the backend child process
   `SIGTERM`, with a short timeout fallback to `SIGKILL` so it never leaks as
   an orphaned process.

## Dev workflow

Keep today's workflow untouched for actual feature work - `npm run dev` (Vite,
port 5173, proxying `/api` to `:8000`) plus `uvicorn backend.main:app --reload`
in a second terminal remains how you iterate on the app day to day.

Add a separate, thin `electron:dev` mode purely for testing the native shell
itself: Electron's main process points the `BrowserWindow` straight at
whichever of `http://localhost:5173` (Vite) or `http://localhost:8000`
(built) is already running, instead of spawning the bundled Python runtime.
This avoids maintaining two parallel dev loops.

## Packaging & distribution

- **Tooling:** Electron Forge, mac-only makers (`@electron-forge/maker-dmg`,
  `@electron-forge/maker-zip`).
- **Icon:** convert `blueprint/assets/icon.svg` to a `.icns` for the app bundle
  and dock icon (Forge/`electron-icon-builder` can do the conversion).
- **Signing:** none for v1, per the locked-in decision above - document the
  right-click > Open bypass for yourself (and Terminal:
  `xattr -cr /Applications/Nutshell.app` if Gatekeeper is stubborn).
- **Output:** a `.dmg` for normal install-by-drag, plus a `.zip` for quick
  manual copies.

## Testing & verification

Per `coding-standards.md`'s test scope rule:

- **Unit-test:** the new pure-logic bits - `ffmpeg_path()` resolution,
  `DATA_ROOT`/`DB_PATH` env-var fallback, the Settings endpoint's `.env`
  read/write. These have real edge cases (env var set vs. unset, missing file)
  and belong in `pytest`.
- **Don't unit-test:** the Electron main process itself (window creation,
  child-process spawn/health-check/kill, port selection). That's
  integration/orchestration glue, not business logic - verify it by actually
  launching the packaged app and the `electron:dev` shell, matching the
  project's existing "browser evidence over assumption" standard.
- **Manual verification checklist** once built: fresh install launches with no
  Python/`ffmpeg`/`node` on the target `PATH`; a full download -> trim ->
  transcribe (local) -> summarize loop works end to end; quitting the app
  leaves no orphaned `python3`/`ffmpeg` process behind (`ps aux | grep
  uvicorn`); a second launch while one is already running focuses the existing
  window instead of double-spawning.

## Risks / watch-outs

- **App size.** The embedded Python runtime plus its installed dependencies
  (`mlx`, `numpy`, the OpenAI/Anthropic SDKs) will likely put the packaged app
  in the several-hundred-MB range before any Whisper model weights are even
  downloaded. Expected and acceptable for a local single-user tool; just don't
  be surprised by it.
- **`mlx-whisper` from a bundled runtime.** Its Metal kernel loading needs to
  be verified from the *actual* embedded-runtime location, not just "it
  imports" - confirm a real transcription run from the packaged app, not only
  from the dev venv.
- **Gatekeeper friction.** Unsigned means a right-click > Open on first launch,
  every time the app is rebuilt with a new signature-less hash (macOS may
  re-flag it). Fine solo; would need revisiting before sharing with anyone
  else.
- **Orphaned backend processes.** Get the quit/kill path right early and test
  it explicitly (see checklist above) - a leaked `uvicorn` process holding the
  SQLite file or the port is the most likely source of "why won't it start"
  confusion later.

## Suggested build order

1. Backend: env-var-driven `DATA_ROOT`/`DB_PATH`/`ffmpeg` path/`.env` path,
   with tests, still fully backward-compatible with the current dev workflow.
2. Electron shell: `electron/` project, main process that spawns an
   *already-installed* dev `venv` Python (not yet the bundled runtime) and
   loads the window - proves the spawn/health-check/kill loop works before
   adding the packaging complexity.
3. Bundled Python runtime + `ffmpeg` build script, wired into Forge's
   `extraResource`.
4. Settings UI for API keys, writing to the `userData` `.env`.
5. Forge packaging (`.dmg`/`.zip`), icon, manual verification checklist.

Each of these is sized like a normal Blueprint feature step even though this
plan itself isn't wired into `build-plan.md` - feel free to run them through
`/fix` or `/feature` individually when you're ready to start.
