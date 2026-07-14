"""Orchestration layer for audio2script.

Single entry point business logic lives behind: the CLI (run.py) and,
later, a web API layer both call these functions and never talk to
adapters or the filesystem cache directly.
"""

from __future__ import annotations

from datetime import datetime, timezone

from generateContents.common.config import SystemConfig
from generateContents.common.logger import get_logger
from generateContents.common.pinyin_converter import to_pinyin
from generateContents.common.schema import ScriptSegment, TranscriptResult
from generateContents.common.sentence_split import split_timed_segments
from generateContents.common.transcript_store import (
    read_transcript,
    transcript_path,
    write_transcript,
)
from generateContents.modules.audio2script.adapters import whisper_client
from generateContents.modules.audio2script.domain.exceptions import TranscriptionError
from generateContents.modules.url2metadata import service as url2metadata_service
from generateContents.modules.url2metadata.domain.schema import VideoMetadata

logger = get_logger(__name__)


def transcribe(metadata: VideoMetadata, config: SystemConfig) -> TranscriptResult:
    logger.info("Starting transcription for content_id=%s", metadata.video_id)

    a2s_config = config.modules.audio2script

    if not metadata.audio_path:
        logger.error("No audio_path on metadata for content_id=%s", metadata.video_id)
        raise TranscriptionError(
            f"No audio_path on metadata for content_id={metadata.video_id}; "
            "run url2metadata with download_audio=true first"
        )

    json_path = transcript_path(config.paths.transcript_dir, metadata.video_id)
    if not a2s_config.overwrite_existing and json_path.is_file():
        try:
            cached = read_transcript(json_path)
        except (OSError, ValueError) as e:
            logger.error("Failed to load cached transcript at %s: %s", json_path, e)
            raise TranscriptionError(f"Failed to load cached transcript at {json_path}") from e
        logger.info("Loaded cached transcript for content_id=%s", metadata.video_id)
        return cached

    try:
        raw_segments = whisper_client.transcribe(
            audio_path=metadata.audio_path,
            model_size=a2s_config.model_size,
            device=a2s_config.device,
            compute_type=a2s_config.compute_type,
            language=a2s_config.language,
        )
    except (RuntimeError, OSError, ValueError) as e:
        logger.error("Failed to transcribe audio for content_id=%s: %s", metadata.video_id, e)
        raise TranscriptionError(
            f"Failed to transcribe audio for content_id={metadata.video_id}"
        ) from e

    sentences = split_timed_segments(raw_segments)

    segments = [
        ScriptSegment(
            index=i,
            start_sec=round(s["start"], 2),
            end_sec=round(s["end"], 2),
            text_zh=s["text"],
            pinyin=to_pinyin(s["text"], a2s_config.pinyin_style),
        )
        for i, s in enumerate(sentences)
    ]

    result = TranscriptResult(
        content_id=metadata.video_id,
        source_type="youtube",
        source_url=metadata.source_url,
        source_audio_path=metadata.audio_path,
        language=a2s_config.language,
        segments=segments,
        transcribed_at=datetime.now(timezone.utc).isoformat(),
    )

    try:
        write_transcript(json_path, result)
    except OSError as e:
        logger.error("Failed to write transcript cache at %s: %s", json_path, e)
        raise TranscriptionError(f"Failed to write transcript cache at {json_path}") from e

    logger.info(
        "Transcription succeeded for content_id=%s (%d segments)",
        metadata.video_id,
        len(segments),
    )
    return result


def run(url: str, config: SystemConfig) -> TranscriptResult:
    """Full pipeline: extract metadata + audio (url2metadata), then transcribe."""
    metadata = url2metadata_service.run(url, config)
    return transcribe(metadata, config)
