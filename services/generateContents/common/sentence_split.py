"""Splits Chinese text on sentence-final punctuation. Shared by every
module that needs sentence-level segments: audio2script splits
pause-bounded Whisper segments further, and script2audio splits
paragraph-style scripts before sending each sentence to TTS."""

from __future__ import annotations

import re

_SENTENCE_END_RE = re.compile(r"[。!?!?]+")


def split_sentences(text: str) -> list[str]:
    """Split raw text into sentences on Chinese/Western sentence-final
    punctuation. Punctuation is kept at the end of each sentence."""
    pieces: list[str] = []
    buf = ""
    for ch in text:
        buf += ch
        if _SENTENCE_END_RE.match(ch):
            pieces.append(buf)
            buf = ""
    if buf.strip():
        pieces.append(buf)
    return [p.strip() for p in pieces if p.strip()]


def split_timed_segments(raw_segments: list[dict]) -> list[dict]:
    """Whisper segments are pause-bounded, not sentence-bounded — split
    further on sentence-final punctuation, distributing each segment's
    [start, end] proportionally by character count."""
    sentences: list[dict] = []

    for seg in raw_segments:
        text = seg["text"]
        start, end = seg["start"], seg["end"]
        duration = end - start
        total_len = len(text) or 1

        cursor = start
        for piece in split_sentences(text):
            piece_duration = duration * (len(piece) / total_len)
            piece_start = cursor
            piece_end = cursor + piece_duration
            cursor = piece_end
            sentences.append({"start": piece_start, "end": piece_end, "text": piece})

    return sentences
