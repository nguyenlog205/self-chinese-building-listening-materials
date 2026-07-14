"""Domain-level errors for url2metadata. No I/O, no third-party dependencies."""

from __future__ import annotations


class MetadataExtractionError(Exception):
    """Raised when video metadata cannot be extracted or parsed."""


class AudioDownloadError(Exception):
    """Raised when audio cannot be downloaded or converted."""
