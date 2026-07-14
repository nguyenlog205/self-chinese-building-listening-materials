"""Loads and validates configs/system.yml and configs/url.yml."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

DEFAULT_CONFIG_PATH = "configs/system.yml"
DEFAULT_URL_LIST_PATH = "configs/url.yml"


class ProjectConfig(BaseModel):
    name: str
    version: str


class PathsConfig(BaseModel):
    metadata_dir: str
    audio_cache_dir: str
    transcript_dir: str
    log_file: str


class Url2MetadataConfig(BaseModel):
    enabled: bool
    download_audio: bool
    audio_format: str
    sample_rate: int
    channels: int
    overwrite_existing: bool


class Audio2ScriptConfig(BaseModel):
    enabled: bool
    model_size: str
    device: str
    compute_type: str
    language: str
    pinyin_style: str
    overwrite_existing: bool


class ModulesConfig(BaseModel):
    url2metadata: Url2MetadataConfig
    audio2script: Audio2ScriptConfig


class LoggingConfig(BaseModel):
    level: str


class SystemConfig(BaseModel):
    project: ProjectConfig
    paths: PathsConfig
    modules: ModulesConfig
    logging: LoggingConfig


class UrlListConfig(BaseModel):
    urls: list[str]


class ConfigLoadError(Exception):
    """Raised when a config file is missing, malformed, or fails validation."""


def load_config(path: str = DEFAULT_CONFIG_PATH) -> SystemConfig:
    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigLoadError(f"Config file not found: {config_path}")

    try:
        raw = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as e:
        raise ConfigLoadError(f"Failed to parse YAML config at {config_path}") from e

    try:
        return SystemConfig.model_validate(raw)
    except ValidationError as e:
        raise ConfigLoadError(f"Invalid config schema in {config_path}: {e}") from e


def load_urls(path: str = DEFAULT_URL_LIST_PATH) -> list[str]:
    url_path = Path(path)
    if not url_path.is_file():
        raise ConfigLoadError(f"URL list file not found: {url_path}")

    try:
        raw = yaml.safe_load(url_path.read_text())
    except yaml.YAMLError as e:
        raise ConfigLoadError(f"Failed to parse YAML url list at {url_path}") from e

    try:
        return UrlListConfig.model_validate(raw).urls
    except ValidationError as e:
        raise ConfigLoadError(f"Invalid url list schema in {url_path}: {e}") from e
