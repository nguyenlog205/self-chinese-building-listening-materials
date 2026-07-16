from __future__ import annotations

from pydantic import BaseModel


class AddLessonRequest(BaseModel):
    url: str


class LessonOut(BaseModel):
    id: str
    source_url: str
    title: str
    status: str
    progress_pct: int
    stage: str
    error_message: str | None = None
    duration_sec: float | None = None
    created_at: str
    last_practiced_at: str | None = None
    segment_count: int = 0


class SegmentOut(BaseModel):
    idx: int
    start_sec: float
    end_sec: float
    text_zh: str
    pinyin: str
