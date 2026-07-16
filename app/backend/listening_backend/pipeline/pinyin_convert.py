"""The only place that imports pypinyin."""

from __future__ import annotations

from pypinyin import Style, pinyin

_STYLE_MAP = {
    "tone_marks": Style.TONE,
    "numeric": Style.TONE3,
}


def to_pinyin(text: str, style: str = "tone_marks") -> str:
    pinyin_style = _STYLE_MAP.get(style, Style.TONE)
    syllables = pinyin(text, style=pinyin_style, errors="ignore")
    return " ".join(s[0] for s in syllables if s)
