"""Reads a pre-written script file (plain UTF-8 text, one sentence or
paragraph per line, `#` lines are comments) into a list of Chinese
sentences ready for TTS. Only place in the codebase that touches script
file I/O."""

from __future__ import annotations

from pathlib import Path

from generateContents.common.sentence_split import split_sentences


def load_sentences(script_path: str) -> list[str]:
    path = Path(script_path)
    if not path.is_file():
        raise FileNotFoundError(f"Script file not found: {script_path}")

    sentences: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        sentences.extend(split_sentences(line))
    return sentences
