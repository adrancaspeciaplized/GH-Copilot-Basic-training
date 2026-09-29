"""Load a JSON configuration file and validate it in a single step."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ConfigFileNotFoundError, ConfigFormatError, ConfigValidationError

logger = logging.getLogger(__name__)

MIN_PORT = 1
MAX_PORT = 65535


@dataclass(frozen=True)
class Config:
    port: int
    host: str
    enable_logging: bool


def load_config(path: str | Path) -> Config:
    """Read ``path``, parse it as JSON and return a validated :class:`Config`.

    Raises:
        ConfigFileNotFoundError: the file is missing or unreadable.
        ConfigFormatError: the content is not a JSON object.
        ConfigValidationError: required fields are missing or have invalid values.
    """
    path = Path(path)
    logger.debug("Loading configuration from %s", path)

    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        logger.error("Configuration file not found: %s", path)
        raise ConfigFileNotFoundError(f"Configuration file not found: {path}") from exc
    except OSError as exc:
        logger.error("Cannot read configuration file %s: %s", path, exc)
        raise ConfigFileNotFoundError(f"Cannot read configuration file {path}: {exc}") from exc

    config = parse_config(text, source=str(path))
    logger.info("Configuration loaded from %s", path)
    return config


def parse_config(text: str, source: str = "<string>") -> Config:
    """Parse a JSON string and validate it into a :class:`Config`."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in %s at line %d column %d", source, exc.lineno, exc.colno)
        raise ConfigFormatError(
            f"Invalid JSON in {source} at line {exc.lineno} column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(data, dict):
        logger.error("Configuration root in %s is not a JSON object", source)
        raise ConfigFormatError(
            f"Configuration root in {source} must be a JSON object, got {type(data).__name__}"
        )

    return _validate(data, source)


def _validate(data: dict[str, Any], source: str) -> Config:
    errors: list[str] = []

    port = data.get("port")
    if "port" not in data:
        errors.append("'port' is required")
    # bool is a subclass of int in Python, so reject it explicitly.
    elif not isinstance(port, int) or isinstance(port, bool):
        errors.append(f"'port' must be an integer, got {type(port).__name__}")
    elif not MIN_PORT <= port <= MAX_PORT:
        errors.append(f"'port' must be between {MIN_PORT} and {MAX_PORT}, got {port}")

    host = data.get("host")
    if "host" not in data:
        errors.append("'host' is required")
    elif not isinstance(host, str):
        errors.append(f"'host' must be a string, got {type(host).__name__}")
    elif not host.strip():
        errors.append("'host' must not be empty")

    enable_logging = data.get("enable_logging")
    if "enable_logging" not in data:
        errors.append("'enable_logging' is required")
    elif not isinstance(enable_logging, bool):
        errors.append(f"'enable_logging' must be a boolean, got {type(enable_logging).__name__}")

    if errors:
        # Log only error descriptions, never raw config values.
        logger.error("Configuration validation failed for %s: %s", source, "; ".join(errors))
        raise ConfigValidationError(errors)

    return Config(port=port, host=host, enable_logging=enable_logging)
