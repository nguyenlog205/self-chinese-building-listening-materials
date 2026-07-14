"""Thin wrapper around edge-tts. Only place in the codebase that imports it."""

from __future__ import annotations

import asyncio

import edge_tts


async def _synthesize(text: str, voice: str, rate: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    audio = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
    return bytes(audio)


def synthesize(text: str, voice: str, rate: str) -> bytes:
    """Synthesize `text` to MP3 bytes using the given edge-tts voice."""
    return asyncio.run(_synthesize(text, voice, rate))
