"""Data model for audio2script transcription output."""

from __future__ import annotations

from pydantic import BaseModel


class ScriptSegment(BaseModel):
    index: int
    start_sec: float
    end_sec: float
    text_zh: str
    pinyin: str


class TranscriptResult(BaseModel):
    video_id: str
    source_audio_path: str
    language: str
    segments: list[ScriptSegment]
    transcribed_at: str
