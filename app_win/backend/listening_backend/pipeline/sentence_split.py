"""Splits Chinese text into sentences on sentence-final punctuation."""

from __future__ import annotations

import re

_SENTENCE_END = re.compile(r"([^。！？!?]+[。！？!?]?)")


def split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    pieces = [p.strip() for p in _SENTENCE_END.findall(text)]
    return [p for p in pieces if p]
