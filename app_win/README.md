# Listening Practice — Windows one-click installer

A separate, Windows-only packaging of the same app as `../app/`, built so an
end user can **download the installer, double-click it, and use the app** —
no Python, Node, or ffmpeg installation required on their machine.

This is achieved by freezing the Python backend into a standalone
`listening-backend.exe` with [PyInstaller](https://pyinstaller.org/) and
bundling a static `ffmpeg.exe`, then wrapping both inside an Electron app
packaged as an NSIS installer.

This directory is a fully independent project from `../app/` — its own copy
of the backend source (with the two Windows-specific adaptations described
below), its own Electron shell, its own frontend copy.

## Important: this can only be built on Windows

PyInstaller does not cross-compile — a Windows `.exe` can only be produced by
running PyInstaller on Windows itself. If you're not on a Windows machine,
use the GitHub Actions workflow:

```
.github/workflows/build-app-win.yml
```

It runs on a `windows-latest` GitHub-hosted runner, triggered automatically
on any push/PR touching `app_win/**`, or manually via the Actions tab
("Run workflow"). The finished installer `.exe` is uploaded as a workflow
artifact — download it from the run's summary page.

**Heads up**: freezing `faster-whisper`/`ctranslate2`/`yt-dlp` with
PyInstaller sometimes needs extra hidden-import fixes that only show up when
you actually run the frozen exe (missing-module errors at runtime, not at
build time). The `.spec` file (`backend/pyinstaller/listening_backend.spec`)
already `collect_all()`s the known-tricky packages, but if the first CI run's
installer fails to start, check the Actions log and the app's console
window for a `ModuleNotFoundError`, then add the missing package to the
`collect_all()` loop in the spec file.

## Building locally (if you do have a Windows machine)

```powershell
cd app_win
npm install                 # installs Electron
npm run dist                 # builds the backend exe, fetches ffmpeg, packages the installer
```

Produces `app_win/dist/*.exe` (NSIS installer, one-click install, no admin
prompt — installs per-user).

To iterate on just the backend without repackaging the whole installer:

```powershell
npm run build:exe            # -> backend/dist/listening-backend/listening-backend.exe
npm run dev                  # launches Electron against that exe directly
```

## What's different from `../app/`

- **No runtime Python needed**: `../app/` creates a venv and `pip install`s
  on first launch (requires the user to have Python + ffmpeg already).
  `app_win/` ships a frozen exe and a bundled `ffmpeg.exe` — nothing to
  install.
- **`config.py`**: detects `sys.frozen` (set by PyInstaller) and stores data
  under `%APPDATA%\ListeningPractice\storage` instead of a path relative to
  the exe, since the install directory isn't guaranteed writable.
- **`pipeline/youtube.py`**: accepts an explicit `ffmpeg_path` (via the
  `LISTENING_FFMPEG_PATH` env var, set by `electron/main.js` to the bundled
  `ffmpeg.exe`) instead of relying on ffmpeg being on the system `PATH`.
- **`electron/main.js`**: spawns the frozen `.exe` directly — no venv
  bootstrap, no bash/PowerShell wrapper script.

## What did NOT change

- Everything else — the FastAPI routes, the SQLite schema, the background
  job/progress-over-WebSocket flow, the frontend (library + practice UI) — is
  an unmodified copy of `../app/`'s equivalent files. See `../app/README.md`
  for how the app works end to end.

## First launch behavior

- The Whisper speech-recognition model is **not** bundled in the installer
  (keeps it smaller). It downloads automatically from Hugging Face the first
  time you add a link — expect a short extra wait and an internet connection
  the very first time, not on every launch.
- The installer is unsigned, so Windows SmartScreen will likely show a
  "Windows protected your PC" warning on first run — this is normal for an
  indie/unsigned app; code-signing is not set up in this v1.
