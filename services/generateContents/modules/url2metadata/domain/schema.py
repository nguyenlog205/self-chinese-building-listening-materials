"""Data model for url2metadata extraction output."""

from __future__ import annotations

from pydantic import BaseModel, Field


class VideoMetadata(BaseModel):
    video_id: str
    source_url: str
    title: str
    uploader: str
    upload_date: str
    duration_sec: int
    description: str
    tags: list[str] = Field(default_factory=list)
    thumbnail_url: str | None = None
    audio_path: str | None = None
    fetched_at: str
