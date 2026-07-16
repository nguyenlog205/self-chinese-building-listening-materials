"""The only place that imports faster_whisper. Transcribes an audio file and
further splits each Whisper segment into sentences, redistributing timestamps
proportionally to character count (matching the format used by the rest of
the app)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

from faster_whisper import WhisperModel

from .sentence_split import split_sentences

ProgressCallback = Callable[[float], None]  # fraction 0..1 of audio processed

_model_cache: dict[tuple[str, str, str], WhisperModel] = {}


@dataclass
class TranscriptSentence:
    start_sec: float
    end_sec: float
    text: str


def _get_model(model_size: str, device: str, compute_type: str) -> WhisperModel:
    key = (model_size, device, compute_type)
    if key not in _model_cache:
        _model_cache[key] = WhisperModel(
            model_size, device=device, compute_type=compute_type
        )
    return _model_cache[key]


def _split_segment(start: float, end: float, text: str) -> Iterator[TranscriptSentence]:
    sentences = split_sentences(text)
    if not sentences:
        return
    total_chars = sum(len(s) for s in sentences) or 1
    cursor = start
    duration = end - start
    for sentence in sentences:
        share = len(sentence) / total_chars * duration
        seg_end = cursor + share
        yield TranscriptSentence(start_sec=cursor, end_sec=seg_end, text=sentence)
        cursor = seg_end


def transcribe(
    audio_path: Path,
    model_size: str,
    device: str,
    compute_type: str,
    language: str,
    on_progress: ProgressCallback | None = None,
) -> list[TranscriptSentence]:
    model = _get_model(model_size, device, compute_type)
    segments, info = model.transcribe(str(audio_path), language=language)

    total_duration = info.duration or 1.0
    sentences: list[TranscriptSentence] = []
    for segment in segments:
        sentences.extend(_split_segment(segment.start, segment.end, segment.text))
        if on_progress:
            on_progress(min(segment.end / total_duration, 1.0))

    return sentences
