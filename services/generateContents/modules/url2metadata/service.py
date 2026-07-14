"""Orchestration layer for url2metadata.

This is the single entry point business logic lives behind: the CLI
(run.py) and, later, a web API layer both call these functions and never
talk to adapters or the filesystem cache directly.
"""

from __future__ import annotations

from datetime import datetime, timezone

import yt_dlp

from generateContents.common.config import SystemConfig
from generateContents.common.logger import get_logger
from generateContents.modules.url2metadata.adapters import cache_store, ytdlp_client
from generateContents.modules.url2metadata.domain.exceptions import (
    AudioDownloadError,
    MetadataExtractionError,
)
from generateContents.modules.url2metadata.domain.schema import VideoMetadata

logger = get_logger(__name__)


def _format_upload_date(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        return datetime.strptime(raw, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        return raw


def _info_to_metadata(url: str, info: dict) -> VideoMetadata:
    return VideoMetadata(
        video_id=info["id"],
        source_url=url,
        title=info.get("title", ""),
        uploader=info.get("uploader", ""),
        upload_date=_format_upload_date(info.get("upload_date")),
        duration_sec=int(info.get("duration") or 0),
        description=info.get("description", ""),
        tags=info.get("tags") or [],
        thumbnail_url=info.get("thumbnail"),
        audio_path=None,
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )


def extract_metadata(url: str, config: SystemConfig) -> VideoMetadata:
    logger.info("Starting metadata extraction for %s", url)

    metadata_dir = config.paths.metadata_dir
    overwrite = config.modules.url2metadata.overwrite_existing

    try:
        info = ytdlp_client.probe(url)
    except yt_dlp.utils.DownloadError as e:
        logger.error("Failed to probe video info for %s: %s", url, e)
        raise MetadataExtractionError(f"Failed to probe video info for {url}") from e

    video_id = info.get("id")
    if not video_id:
        logger.error("yt-dlp did not return a video id for %s", url)
        raise MetadataExtractionError(f"yt-dlp did not return a video id for {url}")

    json_path = cache_store.metadata_path(metadata_dir, video_id)
    if not overwrite and json_path.is_file():
        try:
            cached = cache_store.read_metadata(json_path)
        except (OSError, ValueError) as e:
            logger.error("Failed to load cached metadata at %s: %s", json_path, e)
            raise MetadataExtractionError(
                f"Failed to load cached metadata at {json_path}"
            ) from e
        logger.info("Loaded cached metadata for video_id=%s", video_id)
        return cached

    try:
        metadata = _info_to_metadata(url, info)
    except (KeyError, TypeError, ValueError) as e:
        logger.error("Failed to parse video info for %s: %s", url, e)
        raise MetadataExtractionError(f"Failed to parse video info for {url}") from e

    try:
        cache_store.write_metadata(json_path, metadata)
    except OSError as e:
        logger.error("Failed to write metadata cache at %s: %s", json_path, e)
        raise MetadataExtractionError(
            f"Failed to write metadata cache at {json_path}"
        ) from e

    logger.info("Metadata extraction succeeded for video_id=%s", video_id)
    return metadata


def download_audio(metadata: VideoMetadata, config: SystemConfig) -> VideoMetadata:
    url2metadata_config = config.modules.url2metadata

    if not url2metadata_config.download_audio:
        logger.info(
            "download_audio disabled in config; skipping audio download for video_id=%s",
            metadata.video_id,
        )
        return metadata

    logger.info("Starting audio download for video_id=%s", metadata.video_id)

    wav_path = cache_store.audio_path(config.paths.audio_cache_dir, metadata.video_id)
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = cache_store.metadata_path(config.paths.metadata_dir, metadata.video_id)

    if not url2metadata_config.overwrite_existing and wav_path.is_file():
        logger.info(
            "Cached audio already exists for video_id=%s; skipping download",
            metadata.video_id,
        )
        metadata.audio_path = str(wav_path)
        cache_store.write_metadata(json_path, metadata)
        return metadata

    try:
        ytdlp_client.download_audio(
            source_url=metadata.source_url,
            output_path=wav_path,
            audio_format=url2metadata_config.audio_format,
            sample_rate=url2metadata_config.sample_rate,
            channels=url2metadata_config.channels,
        )
    except yt_dlp.utils.DownloadError as e:
        logger.error("Failed to download audio for video_id=%s: %s", metadata.video_id, e)
        raise AudioDownloadError(
            f"Failed to download audio for video_id={metadata.video_id}"
        ) from e

    if not wav_path.is_file():
        logger.error(
            "Expected audio file not found after download for video_id=%s: %s",
            metadata.video_id,
            wav_path,
        )
        raise AudioDownloadError(
            f"Expected audio file not found after download: {wav_path}"
        )

    metadata.audio_path = str(wav_path)

    try:
        cache_store.write_metadata(json_path, metadata)
    except OSError as e:
        logger.error(
            "Failed to persist updated metadata for video_id=%s: %s", metadata.video_id, e
        )
        raise AudioDownloadError(
            f"Failed to persist updated metadata for video_id={metadata.video_id}"
        ) from e

    logger.info("Audio download succeeded for video_id=%s", metadata.video_id)
    return metadata


def run(url: str, config: SystemConfig) -> VideoMetadata:
    """Full pipeline: extract metadata, then download audio if enabled."""
    metadata = extract_metadata(url, config)
    if config.modules.url2metadata.download_audio:
        metadata = download_audio(metadata, config)
    return metadata
