"""Command line entry point: ``python -m app_config path/to/config.json``."""

import argparse
import logging
import sys

from .errors import ConfigError
from .loader import load_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a JSON configuration file.")
    parser.add_argument("path", help="Path to the JSON configuration file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        config = load_config(args.path)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"OK: host={config.host} port={config.port} enable_logging={config.enable_logging}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
