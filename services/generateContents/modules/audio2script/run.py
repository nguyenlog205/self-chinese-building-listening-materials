"""CLI entry point. Thin wrapper over service.run() — no business logic here."""

from __future__ import annotations

import sys

from generateContents.common.config import SystemConfig, load_config
from generateContents.common.logger import get_logger
from generateContents.modules.audio2script import service
from generateContents.modules.audio2script.domain.schema import TranscriptResult

logger = get_logger(__name__)


def run(url: str, config: SystemConfig | None = None) -> TranscriptResult:
    config = config or load_config()
    logger.info("Starting audio2script run for %s", url)
    result = service.run(url, config)
    logger.info("Completed audio2script run for video_id=%s", result.video_id)
    return result


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m generateContents.modules.audio2script.run <url>", file=sys.stderr)
        sys.exit(1)

    result = run(sys.argv[1])
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
