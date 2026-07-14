"""Domain-level errors for script2audio. No I/O, no third-party dependencies."""

from __future__ import annotations


class ScriptLoadError(Exception):
    """Raised when a script file cannot be found, parsed, or cached."""


class SpeechSynthesisError(Exception):
    """Raised when text-to-speech synthesis or audio export fails."""
