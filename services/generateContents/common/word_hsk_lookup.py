"""Loads HSK reference vocabulary from data/word_hsk/hsk_*.csv and looks up
meaning/level for segmented words.

Each hsk_*.csv has columns Word,Pinyin,POS,Translation. The HSK level is
derived from the filename (hsk_01.csv -> level "1", hsk_79.csv -> the
combined "7-9" band used by the new HSK 3.0 standard).
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

_LEVEL_ALIASES = {"79": "7-9"}


def _level_from_filename(path: Path) -> str:
    digits = re.sub(r"\D", "", path.stem)
    return _LEVEL_ALIASES.get(digits, str(int(digits)) if digits else digits)


def _normalize_pinyin(pinyin: str) -> str:
    return re.sub(r"\s+", "", pinyin).lower()


class WordHskLookup:
    """(word, pinyin) -> (meaning, hsk_level), built once from data/word_hsk/."""

    def __init__(self, word_hsk_dir: str):
        self._by_word_pinyin: dict[tuple[str, str], tuple[str, str]] = {}
        self._by_word: dict[str, tuple[str, str]] = {}

        for path in sorted(Path(word_hsk_dir).glob("hsk_*.csv")):
            level = _level_from_filename(path)
            with path.open(newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    word = (row.get("Word") or "").strip()
                    pinyin = (row.get("Pinyin") or "").strip()
                    meaning = (row.get("Translation") or "").strip()
                    if not word:
                        continue

                    self._by_word.setdefault(word, (meaning, level))

                    key = (word, _normalize_pinyin(pinyin))
                    self._by_word_pinyin.setdefault(key, (meaning, level))

    def lookup(self, word: str, pinyin: str) -> tuple[str, str]:
        """Returns (meaning, hsk_level), both empty strings if not found."""
        exact = self._by_word_pinyin.get((word, _normalize_pinyin(pinyin)))
        if exact is not None:
            return exact

        fallback = self._by_word.get(word)
        if fallback is not None:
            return fallback

        return "", ""
