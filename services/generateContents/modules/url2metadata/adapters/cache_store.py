"""Filesystem cache for metadata JSON and cached audio WAV files."""

from __future__ import annotations

from pathlib import Path

from generateContents.modules.url2metadata.domain.schema import VideoMetadata


def metadata_path(metadata_dir: str, video_id: str) -> Path:
    return Path(metadata_dir) / f"{video_id}.json"


def audio_path(audio_cache_dir: str, video_id: str) -> Path:
    return Path(audio_cache_dir) / f"{video_id}.wav"


def read_metadata(path: Path) -> VideoMetadata:
    return VideoMetadata.model_validate_json(path.read_text())


def write_metadata(path: Path, metadata: VideoMetadata) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(metadata.model_dump_json(indent=2))
