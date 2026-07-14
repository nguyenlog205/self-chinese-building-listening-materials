"""Concatenates per-sentence TTS audio clips into a single WAV track with
a short silence gap between sentences, and reports each sentence's
[start, end] offset in the merged track."""

from __future__ import annotations

from pathlib import Path

from generateContents.common import audio
from generateContents.common.audio import Track


def build(mp3_clips: list[bytes], pause_ms: int) -> tuple[Track, list[tuple[float, float]]]:
    silence = audio.silence(pause_ms)
    track = audio.empty()
    offsets: list[tuple[float, float]] = []
    cursor_ms = 0

    for i, clip_bytes in enumerate(mp3_clips):
        clip = audio.from_mp3_bytes(clip_bytes)
        start_ms = cursor_ms
        end_ms = cursor_ms + len(clip)
        offsets.append((start_ms / 1000, end_ms / 1000))
        track += clip
        cursor_ms = end_ms

        if i < len(mp3_clips) - 1:
            track += silence
            cursor_ms += pause_ms

    return track, offsets


def export_wav(track: Track, path: Path) -> None:
    audio.export_wav(track, path)
