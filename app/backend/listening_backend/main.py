"""FastAPI app factory + uvicorn entrypoint. Prints "READY <port>" to stdout
once the server socket is bound, so the Electron main process knows which
port to point the renderer at."""

from __future__ import annotations

import asyncio
import socket
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import jobs as jobs_api
from .api import lessons as lessons_api
from .api import media as media_api
from .config import ensure_storage_dirs, get_settings
from .db import init_db
from .jobs import set_main_loop


@asynccontextmanager
async def _lifespan(app: FastAPI):
    set_main_loop(asyncio.get_event_loop())
    yield


def create_app() -> FastAPI:
    ensure_storage_dirs()
    init_db()

    app = FastAPI(title="Listening Practice Backend", lifespan=_lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(lessons_api.router)
    app.include_router(jobs_api.router)
    app.include_router(media_api.router)

    @app.get("/health")
    def health() -> dict[str, bool]:
        return {"ok": True}

    return app


app = create_app()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> None:
    settings = get_settings()
    port = settings.port or _free_port()

    config = uvicorn.Config(app, host=settings.host, port=port, log_level="warning")
    server = uvicorn.Server(config)

    async def _run() -> None:
        loop = asyncio.get_event_loop()
        set_main_loop(loop)
        # print once the server has actually bound the socket
        server_task = asyncio.ensure_future(server.serve())
        while not server.started:
            await asyncio.sleep(0.05)
        print(f"READY {port}", flush=True)
        await server_task

    asyncio.run(_run())


if __name__ == "__main__":
    main()
