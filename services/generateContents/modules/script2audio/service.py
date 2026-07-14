"""Orchestration layer for script2audio.

Single entry point business logic lives behind: the CLI (run.py) and,
later, a web API layer both call these functions and never talk to
adapters or the filesystem cache directly.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from generateContents.common.config import SystemConfig
from generateContents.common.logger import get_logger
from generateContents.common.pinyin_converter import to_pinyin
from generateContents.common.schema import ScriptSegment, TranscriptResult
from generateContents.common.transcript_store import (
    read_transcript,
    transcript_path,
    write_transcript,
)
from generateContents.modules.script2audio.adapters import audio_builder, edge_tts_client, script_loader
from generateContents.modules.script2audio.domain.exceptions import ScriptLoadError, SpeechSynthesisError

logger = get_logger(__name__)


def synthesize(script_path: str, config: SystemConfig) -> TranscriptResult:
    content_id = Path(script_path).stem
    logger.info("Starting script2audio synthesis for content_id=%s", content_id)

    s2a_config = config.modules.script2audio

    json_path = transcript_path(config.paths.transcript_dir, content_id)
    if not s2a_config.overwrite_existing and json_path.is_file():
        try:
            cached = read_transcript(json_path)
        except (OSError, ValueError) as e:
            logger.error("Failed to load cached transcript at %s: %s", json_path, e)
            raise ScriptLoadError(f"Failed to load cached transcript at {json_path}") from e
        logger.info("Loaded cached transcript for content_id=%s", content_id)
        return cached

    try:
        sentences = script_loader.load_sentences(script_path)
    except OSError as e:
        logger.error("Failed to load script for content_id=%s: %s", content_id, e)
        raise ScriptLoadError(f"Failed to load script at {script_path}") from e

    if not sentences:
        logger.error("Script has no sentences for content_id=%s", content_id)
        raise ScriptLoadError(f"Script has no sentences: {script_path}")

    try:
        clips = [
            edge_tts_client.synthesize(text, s2a_config.voice, s2a_config.rate)
            for text in sentences
        ]
    except (RuntimeError, OSError) as e:
        logger.error("Failed to synthesize speech for content_id=%s: %s", content_id, e)
        raise SpeechSynthesisError(
            f"Failed to synthesize speech for content_id={content_id}"
        ) from e

    pause_ms = int(s2a_config.pause_between_sentences_sec * 1000)
    track, offsets = audio_builder.build(clips, pause_ms)

    wav_path = Path(config.paths.audio_cache_dir) / f"{content_id}.wav"
    try:
        audio_builder.export_wav(track, wav_path)
    except OSError as e:
        logger.error("Failed to write synthesized audio for content_id=%s: %s", content_id, e)
        raise SpeechSynthesisError(f"Failed to write synthesized audio at {wav_path}") from e

    segments = [
        ScriptSegment(
            index=i,
            start_sec=round(start, 2),
            end_sec=round(end, 2),
            text_zh=text,
            pinyin=to_pinyin(text, s2a_config.pinyin_style),
        )
        for i, (text, (start, end)) in enumerate(zip(sentences, offsets))
    ]

    result = TranscriptResult(
        content_id=content_id,
        source_type="tts",
        source_url=None,
        source_audio_path=str(wav_path),
        language=s2a_config.language,
        segments=segments,
        transcribed_at=datetime.now(timezone.utc).isoformat(),
    )

    try:
        write_transcript(json_path, result)
    except OSError as e:
        logger.error("Failed to write transcript cache at %s: %s", json_path, e)
        raise ScriptLoadError(f"Failed to write transcript cache at {json_path}") from e

    logger.info(
        "Script2audio synthesis succeeded for content_id=%s (%d segments)",
        content_id,
        len(segments),
    )
    return result


def run(script_path: str, config: SystemConfig) -> TranscriptResult:
    return synthesize(script_path, config)
