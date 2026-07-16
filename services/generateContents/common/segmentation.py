"""Thin wrapper around jieba. Only place in the codebase that imports it."""

from __future__ import annotations

import re

import jieba

_HAS_HAN = re.compile(r"[一-鿿]")


def segment_words(text: str) -> list[str]:
    """Split `text` into words, dropping punctuation-only tokens."""
    return [word for word in jieba.cut(text) if _HAS_HAN.search(word)]
