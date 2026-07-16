# Listening Practice (desktop app)

A self-contained Electron desktop app for practicing Chinese listening: paste
a YouTube link, it transcribes it in the background (Whisper + pinyin), and
lets you practice sentence-by-sentence with video, toggleable subtitles/pinyin,
volume control, and optional dictation.

This directory is fully independent of the rest of the repository — its own
pipeline code, its own storage, its own dependencies. It does not import from
or write to `services/`, `data/`, or `outcome/` at the repo root.

```
app/
  backend/     Self-contained Python/FastAPI pipeline + local API server
  electron/    Electron shell (spawns the backend, opens the window)
  frontend/    Plain HTML/CSS/JS renderer UI (library view + practice view)
```

## Prerequisites

- **Python 3.10+** on PATH (`python3` on Linux, `python` on Windows)
- **Node.js 18+** and npm
- **ffmpeg** on PATH (required by yt-dlp/faster-whisper for audio extraction)
  - Fedora: `sudo dnf install ffmpeg`
  - Windows: `winget install ffmpeg` (or download and add to PATH manually)

The Python backend's virtual environment is created automatically on first
run (see `backend/scripts/run.sh` / `run.ps1`) — no manual `pip install`
needed.

## Running in development

```bash
cd app
npm install       # installs Electron into electron/node_modules
npm run dev        # launches Electron, which spawns the Python backend
```

On first launch, Electron's main process runs `backend/scripts/run.sh`
(`run.ps1` on Windows), which creates `backend/.venv/`, installs the backend
package (`pip install -e backend`), and starts the API server on a free local
port. This first run downloads several hundred MB of ML dependencies
(faster-whisper, its CTranslate2 backend, etc.) — subsequent launches are
fast.

## Building an installer

```bash
cd app
npm run build:linux   # produces an AppImage under app/dist/
npm run build:win     # produces an NSIS installer under app/dist/ (run on Windows, or cross-build)
```

**Known v1 limitation**: the built installer still requires the end user to
have Python 3.10+ and ffmpeg on their machine — the backend venv is created
on first launch, it is not frozen into the installer. A fully offline,
single-binary build (PyInstaller-freezing the backend) is a follow-up, not
included in v1.

## Configuration

Backend settings (Whisper model size/device, pinyin style, audio format) live
in `backend/listening_backend/config.py`, overridable via `LISTENING_*`
environment variables, e.g.:

```bash
LISTENING_WHISPER_DEVICE=cuda LISTENING_WHISPER_COMPUTE_TYPE=float16 npm run dev
```

Whisper defaults to CPU (`model_size=base`, `compute_type=int8`) so the app
works out of the box on any machine, GPU or not.

## How it works

1. **Add a link**: the library view (`frontend/index.html`) posts a YouTube
   URL to the backend, which immediately returns a `queued` lesson and starts
   a background job (download audio via yt-dlp → transcribe with
   faster-whisper → split into sentences → convert to pinyin). Progress is
   pushed to the UI over a WebSocket and rendered as a per-lesson progress
   bar.
2. **Practice**: once a lesson is `ready`, opening it (`frontend/practice.html`)
   embeds the actual YouTube video (via the YouTube IFrame API) and steps
   through sentences one at a time — seeking to each sentence's start time and
   auto-pausing at its end. Subtitle and pinyin are hidden by default and can
   be toggled independently; dictation is an optional toggle that grades your
   typed answer character-by-character against the transcript.

Data is stored under `backend/storage/` (SQLite database + cached audio
files) — entirely local, gitignored, and independent of the rest of the repo.
