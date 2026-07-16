"""Packages every cached transcript (data/transcripts/*.json) into a
word-level vocabulary layer under outcome/: one CSV row per unique
(word, pinyin), each with its own standalone TTS audio clip and, where
available, meaning + HSK level looked up from data/word_hsk/.

Additive to export.py: reads the same transcript cache but writes to
outcome/word.csv and outcome/word_audio/, never touching outcome/dataset.csv
or outcome/audio/. Safe to re-run; existing word_audio/ clips are reused
unless modules.word_export.overwrite_existing is set.
"""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

from generateContents.common import audio
from generateContents.common.config import SystemConfig, load_config
from generateContents.common.logger import get_logger
from generateContents.common.pinyin_converter import to_pinyin
from generateContents.common.schema import TranscriptResult
from generateContents.common.segmentation import segment_words
from generateContents.common.word_hsk_lookup import WordHskLookup
from generateContents.modules.script2audio.adapters import edge_tts_client

logger = get_logger(__name__)

CSV_FIELDNAMES = [
    "word",
    "pinyin",
    "meaning",
    "hsk_level",
    "audio_path",
    "audio_source",
]


class WordExportError(Exception):
    """Raised when the word vocabulary dataset cannot be built or written."""


def _load_transcripts(transcript_dir: str) -> list[TranscriptResult]:
    transcripts: list[TranscriptResult] = []
    for path in sorted(Path(transcript_dir).glob("*.json")):
        try:
            transcripts.append(TranscriptResult.model_validate_json(path.read_text()))
        except (OSError, ValueError) as e:
            logger.error("Failed to load transcript at %s: %s", path, e)
            raise WordExportError(f"Failed to load transcript at {path}") from e
    return transcripts


def _audio_filename(word: str, pinyin: str) -> str:
    digest = hashlib.md5(f"{word}\t{pinyin}".encode("utf-8")).hexdigest()[:12]
    return f"{digest}.wav"


def export_words(config: SystemConfig) -> Path:
    logger.info("Starting word vocabulary export")

    transcripts = _load_transcripts(config.paths.transcript_dir)
    if not transcripts:
        logger.error("No cached transcripts found under %s", config.paths.transcript_dir)
        raise WordExportError(f"No cached transcripts found under {config.paths.transcript_dir}")

    word_export_config = config.modules.word_export
    hsk_lookup = WordHskLookup(config.paths.word_hsk_dir)

    outcome_dir = Path(config.paths.outcome_dir)
    word_audio_dir = outcome_dir / "word_audio"

    unique_words: dict[tuple[str, str], None] = {}
    for result in transcripts:
        for segment in result.segments:
            for word in segment_words(segment.text_zh):
                pinyin = to_pinyin(word, word_export_config.pinyin_style)
                unique_words.setdefault((word, pinyin), None)

    rows: list[dict] = []
    for word, pinyin in unique_words:
        meaning, hsk_level = hsk_lookup.lookup(word, pinyin)

        audio_filename = _audio_filename(word, pinyin)
        audio_file_path = word_audio_dir / audio_filename
        if word_export_config.overwrite_existing or not audio_file_path.is_file():
            try:
                clip_bytes = edge_tts_client.synthesize(
                    word, word_export_config.voice, word_export_config.rate
                )
                clip = audio.from_mp3_bytes(clip_bytes)
                audio.export_wav(clip, audio_file_path)
            except (RuntimeError, OSError) as e:
                logger.error("Failed to synthesize audio for word=%r: %s", word, e)
                raise WordExportError(f"Failed to synthesize audio for word={word!r}") from e

        rows.append(
            {
                "word": word,
                "pinyin": pinyin,
                "meaning": meaning,
                "hsk_level": hsk_level,
                "audio_path": f"word_audio/{audio_filename}",
                "audio_source": "tts",
            }
        )

    csv_path = outcome_dir / "word.csv"
    try:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
    except OSError as e:
        logger.error("Failed to write word CSV at %s: %s", csv_path, e)
        raise WordExportError(f"Failed to write word CSV at {csv_path}") from e

    logger.info(
        "Word vocabulary export succeeded: %d content item(s), %d unique word(s) -> %s",
        len(transcripts),
        len(rows),
        outcome_dir,
    )
    return csv_path


def main() -> None:
    config = load_config()
    try:
        csv_path = export_words(config)
    except WordExportError as e:
        print(f"Word export failed: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Word vocabulary dataset written to {csv_path}")


if __name__ == "__main__":
    main()
