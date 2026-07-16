"""App-wide settings. Storage lives under %APPDATA%/ListeningPractice when
running as a frozen PyInstaller exe (the install directory may not be
writable, and per-user AppData is the Windows convention); under
backend/storage/ during local/dev runs of the plain Python source."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _storage_dir() -> Path:
    if getattr(sys, "frozen", False):
        appdata = os.environ.get("APPDATA") or str(Path.home())
        return Path(appdata) / "ListeningPractice" / "storage"
    return BACKEND_DIR / "storage"


STORAGE_DIR = _storage_dir()
AUDIO_CACHE_DIR = STORAGE_DIR / "audio_cache"
DB_PATH = STORAGE_DIR / "listening.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LISTENING_")

    host: str = "127.0.0.1"
    port: int = 0  # 0 = let the OS pick a free port; printed on startup

    whisper_model_size: str = "base"  # tiny | base | small | medium | large-v3
    whisper_device: str = "cpu"  # cpu | cuda
    whisper_compute_type: str = "int8"  # int8 (cpu) | float16 (cuda)
    whisper_language: str = "zh"

    pinyin_style: str = "tone_marks"  # tone_marks | numeric

    audio_sample_rate: int = 16000
    audio_channels: int = 1

    ffmpeg_path: str | None = None  # explicit path to ffmpeg.exe; None = rely on PATH


def get_settings() -> Settings:
    return Settings()


def ensure_storage_dirs() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
