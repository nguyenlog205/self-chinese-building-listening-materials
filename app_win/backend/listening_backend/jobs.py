"""In-process background job runner. Each "add lesson" request spawns one
thread that walks the pipeline (download -> transcribe -> segment), writing
status/progress to SQLite and broadcasting the same events to any connected
WebSocket listeners for that lesson."""

from __future__ import annotations

import asyncio
import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from .config import Settings, ensure_storage_dirs
from .db import get_conn
from .pipeline import youtube
from .pipeline.pinyin_convert import to_pinyin
from .pipeline.transcribe import transcribe

_executor = ThreadPoolExecutor(max_workers=2)

# lesson_id -> set of asyncio.Queue used to push progress events to WS clients
_listeners: dict[str, set[asyncio.Queue]] = {}
_listeners_lock = threading.Lock()
_main_loop: asyncio.AbstractEventLoop | None = None


def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _main_loop
    _main_loop = loop


def subscribe(lesson_id: str) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue()
    with _listeners_lock:
        _listeners.setdefault(lesson_id, set()).add(queue)
    return queue


def unsubscribe(lesson_id: str, queue: asyncio.Queue) -> None:
    with _listeners_lock:
        listeners = _listeners.get(lesson_id)
        if listeners:
            listeners.discard(queue)
            if not listeners:
                _listeners.pop(lesson_id, None)


def _broadcast(lesson_id: str, event: dict[str, Any]) -> None:
    if _main_loop is None:
        return
    with _listeners_lock:
        queues = list(_listeners.get(lesson_id, ()))
    for queue in queues:
        _main_loop.call_soon_threadsafe(queue.put_nowait, event)


def _update_status(
    conn: sqlite3.Connection,
    lesson_id: str,
    *,
    status: str,
    stage: str,
    progress_pct: int,
    error_message: str | None = None,
    title: str | None = None,
    duration_sec: float | None = None,
) -> None:
    fields = ["status = ?", "stage = ?", "progress_pct = ?", "error_message = ?"]
    params: list[Any] = [status, stage, progress_pct, error_message]
    if title is not None:
        fields.append("title = ?")
        params.append(title)
    if duration_sec is not None:
        fields.append("duration_sec = ?")
        params.append(duration_sec)
    params.append(lesson_id)
    conn.execute(f"UPDATE lessons SET {', '.join(fields)} WHERE id = ?", params)


def _report(
    lesson_id: str, *, status: str, stage: str, progress_pct: int, error_message: str | None = None
) -> None:
    with get_conn() as conn:
        _update_status(
            conn,
            lesson_id,
            status=status,
            stage=stage,
            progress_pct=progress_pct,
            error_message=error_message,
        )
    _broadcast(
        lesson_id,
        {
            "status": status,
            "stage": stage,
            "progress_pct": progress_pct,
            "error_message": error_message,
        },
    )


def _run_pipeline(lesson_id: str, url: str, settings: Settings) -> None:
    ensure_storage_dirs()
    try:
        _report(lesson_id, status="downloading", stage="metadata", progress_pct=2)
        info = youtube.extract_info(url)

        with get_conn() as conn:
            _update_status(
                conn,
                lesson_id,
                status="downloading",
                stage="audio",
                progress_pct=10,
                title=info.title,
                duration_sec=info.duration_sec,
            )
        _broadcast(
            lesson_id,
            {"status": "downloading", "stage": "audio", "progress_pct": 10, "title": info.title},
        )

        audio_path = youtube.download_audio(
            info.video_id,
            url,
            settings.audio_sample_rate,
            settings.audio_channels,
            ffmpeg_path=settings.ffmpeg_path,
        )
        _report(lesson_id, status="transcribing", stage="transcribing", progress_pct=40)

        def on_progress(fraction: float) -> None:
            pct = 40 + int(fraction * 50)
            _report(lesson_id, status="transcribing", stage="transcribing", progress_pct=pct)

        sentences = transcribe(
            audio_path,
            model_size=settings.whisper_model_size,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
            language=settings.whisper_language,
            on_progress=on_progress,
        )

        _report(lesson_id, status="segmenting", stage="segmenting", progress_pct=92)
        with get_conn() as conn:
            for idx, sentence in enumerate(sentences):
                conn.execute(
                    """INSERT INTO segments (lesson_id, idx, start_sec, end_sec, text_zh, pinyin)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        lesson_id,
                        idx,
                        sentence.start_sec,
                        sentence.end_sec,
                        sentence.text,
                        to_pinyin(sentence.text, settings.pinyin_style),
                    ),
                )
            _update_status(
                conn, lesson_id, status="ready", stage="done", progress_pct=100
            )
        _broadcast(lesson_id, {"status": "ready", "stage": "done", "progress_pct": 100})
    except Exception as exc:  # noqa: BLE001 - a failed lesson must not crash the app
        _report(
            lesson_id,
            status="error",
            stage="error",
            progress_pct=0,
            error_message=str(exc),
        )


def start_job(lesson_id: str, url: str, settings: Settings) -> None:
    _executor.submit(_run_pipeline, lesson_id, url, settings)
