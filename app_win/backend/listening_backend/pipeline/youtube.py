"""The only place that imports yt-dlp. Fetches metadata and downloads audio
for a YouTube URL, writing a mono WAV to storage/audio_cache/{video_id}.wav."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yt_dlp

from ..config import AUDIO_CACHE_DIR


class MetadataExtractionError(Exception):
    pass


class AudioDownloadError(Exception):
    pass


@dataclass
class VideoInfo:
    video_id: str
    title: str
    duration_sec: float
    source_url: str


def extract_info(url: str) -> VideoInfo:
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:  # noqa: BLE001 - surfaced to the job/error state
        raise MetadataExtractionError(str(exc)) from exc

    return VideoInfo(
        video_id=info["id"],
        title=info.get("title", info["id"]),
        duration_sec=float(info.get("duration") or 0),
        source_url=url,
    )


def download_audio(
    video_id: str,
    url: str,
    sample_rate: int,
    channels: int,
    ffmpeg_path: str | None = None,
) -> Path:
    """Downloads and converts the video's audio to a mono WAV at sample_rate,
    reusing the cached file if it already exists. ffmpeg_path points yt-dlp at
    a specific ffmpeg binary (the bundled one in the frozen build) instead of
    relying on it being present on PATH."""
    out_path = AUDIO_CACHE_DIR / f"{video_id}.wav"
    if out_path.exists():
        return out_path

    AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp_template = str(AUDIO_CACHE_DIR / f"{video_id}.%(ext)s")
    ydl_opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "outtmpl": tmp_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
        "postprocessor_args": [
            "-ar",
            str(sample_rate),
            "-ac",
            str(channels),
        ],
    }
    if ffmpeg_path:
        ydl_opts["ffmpeg_location"] = ffmpeg_path
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as exc:  # noqa: BLE001
        raise AudioDownloadError(str(exc)) from exc

    if not out_path.exists():
        raise AudioDownloadError(f"Expected output file not found: {out_path}")
    return out_path
