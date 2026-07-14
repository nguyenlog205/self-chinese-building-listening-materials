"""Packages every cached transcript (data/transcripts/*.json, regardless
of whether it came from audio2script or script2audio) into a
self-contained dataset under outcome/: one CSV row per sentence, and one
audio clip per row cut from that sentence's source recording.

This is a separate step from pipeline.py — it does not fetch, transcribe,
or synthesize anything; it only reads what has already been cached and
re-packages it. Safe to re-run any time; it always rebuilds outcome/ from
the current cache.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from generateContents.common import audio
from generateContents.common.config import SystemConfig, load_config
from generateContents.common.logger import get_logger
from generateContents.common.schema import TranscriptResult

logger = get_logger(__name__)

CSV_FIELDNAMES = [
    "content_id",
    "source_type",
    "source_url",
    "index",
    "start_sec",
    "end_sec",
    "text_zh",
    "pinyin",
    "audio_path",
]


class ExportError(Exception):
    """Raised when the outcome dataset cannot be built or written."""


def _load_transcripts(transcript_dir: str) -> list[TranscriptResult]:
    transcripts: list[TranscriptResult] = []
    for path in sorted(Path(transcript_dir).glob("*.json")):
        try:
            transcripts.append(TranscriptResult.model_validate_json(path.read_text()))
        except (OSError, ValueError) as e:
            logger.error("Failed to load transcript at %s: %s", path, e)
            raise ExportError(f"Failed to load transcript at {path}") from e
    return transcripts


def export_dataset(config: SystemConfig) -> Path:
    logger.info("Starting dataset export")

    transcripts = _load_transcripts(config.paths.transcript_dir)
    if not transcripts:
        logger.error("No cached transcripts found under %s", config.paths.transcript_dir)
        raise ExportError(f"No cached transcripts found under {config.paths.transcript_dir}")

    outcome_dir = Path(config.paths.outcome_dir)
    audio_dir = outcome_dir / "audio"

    rows: list[dict] = []
    for result in transcripts:
        try:
            track = audio.load_wav(result.source_audio_path)
        except (OSError, ValueError) as e:
            logger.error(
                "Failed to load source audio for content_id=%s: %s", result.content_id, e
            )
            raise ExportError(
                f"Failed to load source audio for content_id={result.content_id}"
            ) from e

        for segment in result.segments:
            audio_filename = f"{result.content_id}_{segment.index:03d}.wav"
            clip = audio.slice_ms(
                track, int(segment.start_sec * 1000), int(segment.end_sec * 1000)
            )
            try:
                audio.export_wav(clip, audio_dir / audio_filename)
            except OSError as e:
                logger.error(
                    "Failed to export audio clip for content_id=%s index=%d: %s",
                    result.content_id,
                    segment.index,
                    e,
                )
                raise ExportError(
                    f"Failed to export audio clip for content_id={result.content_id} "
                    f"index={segment.index}"
                ) from e

            rows.append(
                {
                    "content_id": result.content_id,
                    "source_type": result.source_type,
                    "source_url": result.source_url or "",
                    "index": segment.index,
                    "start_sec": segment.start_sec,
                    "end_sec": segment.end_sec,
                    "text_zh": segment.text_zh,
                    "pinyin": segment.pinyin,
                    "audio_path": f"audio/{audio_filename}",
                }
            )

    csv_path = outcome_dir / "dataset.csv"
    try:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
    except OSError as e:
        logger.error("Failed to write dataset CSV at %s: %s", csv_path, e)
        raise ExportError(f"Failed to write dataset CSV at {csv_path}") from e

    logger.info(
        "Dataset export succeeded: %d content item(s), %d sample(s) -> %s",
        len(transcripts),
        len(rows),
        outcome_dir,
    )
    return csv_path


def main() -> None:
    config = load_config()
    try:
        csv_path = export_dataset(config)
    except ExportError as e:
        print(f"Export failed: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Dataset written to {csv_path}")


if __name__ == "__main__":
    main()
