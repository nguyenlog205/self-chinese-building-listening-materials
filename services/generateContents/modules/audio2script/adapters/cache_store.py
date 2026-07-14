"""Filesystem cache for transcript JSON files."""

from __future__ import annotations

from pathlib import Path

from generateContents.modules.audio2script.domain.schema import TranscriptResult


def transcript_path(transcript_dir: str, video_id: str) -> Path:
    return Path(transcript_dir) / f"{video_id}.json"


def read_transcript(path: Path) -> TranscriptResult:
    return TranscriptResult.model_validate_json(path.read_text())


def write_transcript(path: Path, result: TranscriptResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result.model_dump_json(indent=2))
