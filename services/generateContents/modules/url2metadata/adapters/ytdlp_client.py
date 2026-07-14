"""Thin wrapper around yt-dlp. Only place in the codebase that imports yt-dlp.

Raises yt_dlp's own exceptions unmodified — translation into domain
exceptions (MetadataExtractionError / AudioDownloadError) happens in
service.py, keeping this adapter swappable for a different backend later.
"""

from __future__ import annotations

from pathlib import Path

import yt_dlp


def probe(url: str) -> dict:
    """Fetch raw video info without downloading anything."""
    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        return ydl.extract_info(url, download=False)


def download_audio(
    source_url: str,
    output_path: Path,
    audio_format: str,
    sample_rate: int,
    channels: int,
) -> None:
    """Download best audio for `source_url` and convert it to a WAV at `output_path`."""
    ydl_opts = {
        "quiet": True,
        "noprogress": True,
        "format": "bestaudio/best",
        "outtmpl": str(output_path.with_suffix("")) + ".%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
            }
        ],
        "postprocessor_args": {
            "ffmpeg": [
                "-ar", str(sample_rate),
                "-ac", str(channels),
            ],
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([source_url])
