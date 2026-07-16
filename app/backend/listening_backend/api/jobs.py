from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .. import jobs as jobs_module
from ..db import get_conn

router = APIRouter(tags=["jobs"])


@router.websocket("/ws/jobs/{lesson_id}")
async def job_progress(websocket: WebSocket, lesson_id: str) -> None:
    await websocket.accept()

    with get_conn() as conn:
        row = conn.execute(
            "SELECT status, stage, progress_pct, error_message FROM lessons WHERE id = ?",
            (lesson_id,),
        ).fetchone()
    if row is not None:
        await websocket.send_json(
            {
                "status": row["status"],
                "stage": row["stage"],
                "progress_pct": row["progress_pct"],
                "error_message": row["error_message"],
            }
        )
        if row["status"] in ("ready", "error"):
            await websocket.close()
            return

    queue = jobs_module.subscribe(lesson_id)
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
            if event.get("status") in ("ready", "error"):
                break
    except WebSocketDisconnect:
        pass
    finally:
        jobs_module.unsubscribe(lesson_id, queue)
