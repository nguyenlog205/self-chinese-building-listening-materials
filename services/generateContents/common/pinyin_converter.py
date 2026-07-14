"""Thin wrapper around pypinyin. Only place in the codebase that imports it."""

from __future__ import annotations

from pypinyin import Style, pinyin

_STYLE_MAP = {
    "tone_marks": Style.TONE,
    "numeric": Style.TONE3,
}


def to_pinyin(text: str, style: str) -> str:
    pinyin_style = _STYLE_MAP[style]
    syllables = pinyin(text, style=pinyin_style, errors="ignore")
    return " ".join(s[0] for s in syllables)
