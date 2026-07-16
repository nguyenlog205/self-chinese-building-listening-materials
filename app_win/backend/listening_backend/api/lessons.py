from __future__ import annotations

import sqlite3

from fastapi import APIRouter, HTTPException

from .. import jobs
from ..config import get_settings
from ..db import get_conn
from ..models import AddLessonRequest, LessonOut, SegmentOut
from ..pipeline import youtube
from ..pipeline.youtube import MetadataExtractionError

router = APIRouter(prefix="/api/lessons", tags=["lessons"])


def _lesson_row_to_out(conn: sqlite3.Connection, row: sqlite3.Row) -> LessonOut:
    count = conn.execute(
        "SELECT COUNT(*) FROM segments WHERE lesson_id = ?", (row["id"],)
    ).fetchone()[0]
    return LessonOut(
        id=row["id"],
        source_url=row["source_url"],
        title=row["title"],
        status=row["status"],
        progress_pct=row["progress_pct"],
        stage=row["stage"],
        error_message=row["error_message"],
        duration_sec=row["duration_sec"],
        created_at=row["created_at"],
        last_practiced_at=row["last_practiced_at"],
        segment_count=count,
    )


@router.post("", response_model=LessonOut)
def add_lesson(payload: AddLessonRequest) -> LessonOut:
    try:
        info = youtube.extract_info(payload.url)
    except MetadataExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT * FROM lessons WHERE id = ?", (info.video_id,)
        ).fetchone()
        if existing is not None:
            return _lesson_row_to_out(conn, existing)

        conn.execute(
            """INSERT INTO lessons (id, source_url, title, status, stage, duration_sec)
               VALUES (?, ?, ?, 'queued', 'queued', ?)""",
            (info.video_id, payload.url, info.title, info.duration_sec),
        )
        row = conn.execute(
            "SELECT * FROM lessons WHERE id = ?", (info.video_id,)
        ).fetchone()
        out = _lesson_row_to_out(conn, row)

    jobs.start_job(info.video_id, payload.url, get_settings())
    return out


@router.get("", response_model=list[LessonOut])
def list_lessons() -> list[LessonOut]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM lessons ORDER BY created_at DESC"
        ).fetchall()
        return [_lesson_row_to_out(conn, row) for row in rows]


@router.get("/{lesson_id}", response_model=LessonOut)
def get_lesson(lesson_id: str) -> LessonOut:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM lessons WHERE id = ?", (lesson_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return _lesson_row_to_out(conn, row)


@router.get("/{lesson_id}/segments", response_model=list[SegmentOut])
def get_segments(lesson_id: str) -> list[SegmentOut]:
    with get_conn() as conn:
        lesson = conn.execute(
            "SELECT id FROM lessons WHERE id = ?", (lesson_id,)
        ).fetchone()
        if lesson is None:
            raise HTTPException(status_code=404, detail="Lesson not found")
        rows = conn.execute(
            "SELECT * FROM segments WHERE lesson_id = ? ORDER BY idx",
            (lesson_id,),
        ).fetchall()
        return [
            SegmentOut(
                idx=r["idx"],
                start_sec=r["start_sec"],
                end_sec=r["end_sec"],
                text_zh=r["text_zh"],
                pinyin=r["pinyin"],
            )
            for r in rows
        ]


@router.post("/{lesson_id}/practiced", response_model=LessonOut)
def mark_practiced(lesson_id: str) -> LessonOut:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM lessons WHERE id = ?", (lesson_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Lesson not found")
        conn.execute(
            "UPDATE lessons SET last_practiced_at = datetime('now') WHERE id = ?",
            (lesson_id,),
        )
        row = conn.execute(
            "SELECT * FROM lessons WHERE id = ?", (lesson_id,)
        ).fetchone()
        return _lesson_row_to_out(conn, row)


@router.delete("/{lesson_id}")
def delete_lesson(lesson_id: str) -> dict[str, bool]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM lessons WHERE id = ?", (lesson_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Lesson not found")
        conn.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
    return {"deleted": True}
