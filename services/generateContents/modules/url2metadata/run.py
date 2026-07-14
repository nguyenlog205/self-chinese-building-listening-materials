"""CLI entry point. Thin wrapper over service.run() — no business logic here."""

from __future__ import annotations

import sys

from generateContents.common.config import SystemConfig, load_config
from generateContents.common.logger import get_logger
from generateContents.modules.url2metadata import service
from generateContents.modules.url2metadata.domain.schema import VideoMetadata

logger = get_logger(__name__)


def run(url: str, config: SystemConfig | None = None) -> VideoMetadata:
    config = config or load_config()
    logger.info("Starting url2metadata run for %s", url)
    metadata = service.run(url, config)
    logger.info("Completed url2metadata run for video_id=%s", metadata.video_id)
    return metadata


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m generateContents.modules.url2metadata.run <url>", file=sys.stderr)
        sys.exit(1)

    metadata = run(sys.argv[1])
    print(metadata.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
