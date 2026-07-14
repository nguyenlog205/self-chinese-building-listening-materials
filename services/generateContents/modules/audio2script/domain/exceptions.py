"""Domain-level errors for audio2script. No I/O, no third-party dependencies."""

from __future__ import annotations


class TranscriptionError(Exception):
    """Raised when audio cannot be transcribed or the result cannot be parsed."""
