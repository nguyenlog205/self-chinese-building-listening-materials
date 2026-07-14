"""Batch entry point: run the full content pipeline (metadata -> audio ->
transcript) for every URL listed in configs/url.yml, in order.

One failing URL does not stop the batch — failures are collected and
reported at the end so a bad video in the middle of a long list doesn't
waste the work already done on the others.
"""

from __future__ import annotations

import sys

from generateContents.common.config import load_config, load_urls
from generateContents.common.logger import get_logger
from generateContents.modules.audio2script import service as audio2script_service
from generateContents.modules.audio2script.domain.exceptions import TranscriptionError
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


def main() -> None:
    results = run_batch()

    ok_count = sum(1 for status in results.values() if status.startswith("ok"))
    failed_count = len(results) - ok_count

    print(f"\n{ok_count} succeeded, {failed_count} failed\n")
    for url, status in results.items():
        print(f"  [{status}] {url}")

    if failed_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
