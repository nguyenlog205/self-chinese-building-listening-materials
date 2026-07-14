"""Shared output schema for learning material. Every content source
(audio2script, script2audio, ...) produces a TranscriptResult in this
format, so downstream consumers don't need to know which source a given
piece of content came from."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

SourceType = Literal["youtube", "tts"]


class ScriptSegment(BaseModel):
    index: int
    start_sec: float
    end_sec: float
    text_zh: str
    pinyin: str


class TranscriptResult(BaseModel):
    content_id: str
    source_type: SourceType
    source_url: str | None = None
    source_audio_path: str
    language: str
    segments: list[ScriptSegment]
    transcribed_at: str
