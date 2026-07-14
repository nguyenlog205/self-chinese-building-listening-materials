"""Filesystem cache for transcript JSON files. Shared by every module
that produces a TranscriptResult (audio2script, script2audio, ...), since
they all write to the same data/transcripts/{content_id}.json location."""

from __future__ import annotations

from pathlib import Path

from generateContents.common.schema import TranscriptResult


def transcript_path(transcript_dir: str, content_id: str) -> Path:
    return Path(transcript_dir) / f"{content_id}.json"


def read_transcript(path: Path) -> TranscriptResult:
    return TranscriptResult.model_validate_json(path.read_text())


def write_transcript(path: Path, result: TranscriptResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result.model_dump_json(indent=2))
