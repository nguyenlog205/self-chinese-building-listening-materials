"""CLI entry point. Thin wrapper over service.run() — no business logic here."""

from __future__ import annotations

import sys

from generateContents.common.config import SystemConfig, load_config
from generateContents.common.logger import get_logger
from generateContents.common.schema import TranscriptResult
from generateContents.modules.script2audio import service

logger = get_logger(__name__)


def run(script_path: str, config: SystemConfig | None = None) -> TranscriptResult:
    config = config or load_config()
    logger.info("Starting script2audio run for %s", script_path)
    result = service.run(script_path, config)
    logger.info("Completed script2audio run for content_id=%s", result.content_id)
    return result


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m generateContents.modules.script2audio.run <script_path>", file=sys.stderr)
        sys.exit(1)

    result = run(sys.argv[1])
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
