"""Batch entry point: run the full content pipeline for every source
listed in configs/. Two independent batches run: url2metadata -> audio2script
for every URL in configs/url.yml, and script2audio for every script in
configs/scripts.yml.

One failing item does not stop its batch — failures are collected and
reported at the end so a bad video or script in the middle of a long list
doesn't waste the work already done on the others.
"""

from __future__ import annotations

import sys

from generateContents.common.config import load_config, load_scripts, load_urls
from generateContents.common.logger import get_logger
from generateContents.modules.audio2script import service as audio2script_service
from generateContents.modules.audio2script.domain.exceptions import TranscriptionError
from generateContents.modules.script2audio import service as script2audio_service
from generateContents.modules.script2audio.domain.exceptions import ScriptLoadError, SpeechSynthesisError
from generateContents.modules.url2metadata.domain.exceptions import (
    AudioDownloadError,
    MetadataExtractionError,
)

logger = get_logger(__name__)


def run_batch(urls: list[str] | None = None) -> dict[str, str]:
    config = load_config()
    urls = urls if urls is not None else load_urls()

    logger.info("Starting batch pipeline for %d URL(s)", len(urls))

    results: dict[str, str] = {}
    for url in urls:
        logger.info("Processing %s", url)
        try:
            result = audio2script_service.run(url, config)
        except (MetadataExtractionError, AudioDownloadError, TranscriptionError) as e:
            logger.error("Failed to process %s: %s", url, e)
            results[url] = f"failed: {e}"
            continue
        results[url] = f"ok: {len(result.segments)} segments"

    ok_count = sum(1 for status in results.values() if status.startswith("ok"))
    logger.info("Batch pipeline finished: %d/%d succeeded", ok_count, len(urls))
    return results


def run_script_batch(script_paths: list[str] | None = None) -> dict[str, str]:
    config = load_config()
    script_paths = script_paths if script_paths is not None else load_scripts()

    logger.info("Starting batch pipeline for %d script(s)", len(script_paths))

    results: dict[str, str] = {}
    for script_path in script_paths:
        logger.info("Processing %s", script_path)
        try:
            result = script2audio_service.run(script_path, config)
        except (ScriptLoadError, SpeechSynthesisError) as e:
            logger.error("Failed to process %s: %s", script_path, e)
            results[script_path] = f"failed: {e}"
            continue
        results[script_path] = f"ok: {len(result.segments)} segments"

    ok_count = sum(1 for status in results.values() if status.startswith("ok"))
    logger.info("Script batch pipeline finished: %d/%d succeeded", ok_count, len(script_paths))
    return results


def main() -> None:
    results = run_batch()
    results.update(run_script_batch())

    ok_count = sum(1 for status in results.values() if status.startswith("ok"))
    failed_count = len(results) - ok_count

    print(f"\n{ok_count} succeeded, {failed_count} failed\n")
    for source, status in results.items():
        print(f"  [{status}] {source}")

    if failed_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
