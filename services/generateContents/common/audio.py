"""Thin wrapper around pydub. Only place in the codebase that imports it."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from pydub import AudioSegment

Track = AudioSegment


def from_mp3_bytes(data: bytes) -> Track:
    return AudioSegment.from_file(BytesIO(data), format="mp3")


def load_wav(path: str) -> Track:
    return AudioSegment.from_file(path, format="wav")


def silence(duration_ms: int) -> Track:
    return AudioSegment.silent(duration=duration_ms)


def empty() -> Track:
    return AudioSegment.empty()


def slice_ms(track: Track, start_ms: int, end_ms: int) -> Track:
    return track[start_ms:end_ms]


def export_wav(track: Track, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    track.export(path, format="wav")
