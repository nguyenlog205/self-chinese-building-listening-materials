"""Shared logger setup, configured from SystemConfig.logging and paths.log_file."""

from __future__ import annotations

import logging
from pathlib import Path

from generateContents.common.config import SystemConfig, load_config

_configured = False


def _configure_root(config: SystemConfig) -> None:
    global _configured
    if _configured:
        return

    log_path = Path(config.paths.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, config.logging.level.upper(), logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    _configured = True


def get_logger(name: str, config: SystemConfig | None = None) -> logging.Logger:
    _configure_root(config or load_config())
    return logging.getLogger(name)
