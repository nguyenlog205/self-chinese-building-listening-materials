"""Thin wrapper around faster-whisper. Only place in the codebase that
imports faster-whisper.

The model is cached per (model_size, device, compute_type) so repeated
calls within the same process (e.g. the API server) don't reload multi-GB
weights on every request.
"""

from __future__ import annotations

from functools import lru_cache

from faster_whisper import WhisperModel


@lru_cache(maxsize=4)
def _load_model(model_size: str, device: str, compute_type: str) -> WhisperModel:
    return WhisperModel(model_size, device=device, compute_type=compute_type)


def transcribe(
    audio_path: str,
    model_size: str,
    device: str,
    compute_type: str,
    language: str,
) -> list[dict]:
    """Transcribe `audio_path`, returning raw whisper segments as dicts."""
    model = _load_model(model_size, device, compute_type)
    segments, _info = model.transcribe(audio_path, language=language, vad_filter=True)
    return [{"start": seg.start, "end": seg.end, "text": seg.text.strip()} for seg in segments]
