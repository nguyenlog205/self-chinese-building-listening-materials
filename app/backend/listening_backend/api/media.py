from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..config import AUDIO_CACHE_DIR

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/audio/{lesson_id}.wav")
def get_audio(lesson_id: str) -> FileResponse:
    path = AUDIO_CACHE_DIR / f"{lesson_id}.wav"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(path, media_type="audio/wav")
