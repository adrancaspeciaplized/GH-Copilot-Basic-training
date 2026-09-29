# app-config

Loads a JSON configuration file and validates it in one step.

## Config format

```json
{ "port": 8080, "host": "localhost", "enable_logging": true }
```

| Field | Type | Rules |
|---|---|---|
| `port` | int | required, 1–65535, booleans rejected |
| `host` | string | required, non-empty |
| `enable_logging` | bool | required |

Unknown fields are ignored.

## Usage

```python
from app_config import load_config, ConfigError

try:
    config = load_config("config.json")
except ConfigError as exc:
    ...
```

CLI: `python -m app_config config.example.json [-v]`

## Errors

All errors inherit from `ConfigError`:

- `ConfigFileNotFoundError`: the file is missing or can't be read
- `ConfigFormatError`: the content is invalid JSON or the root is not an object
- `ConfigValidationError`: fields are missing or wrong; `.errors` lists every problem

## Logging

Uses the standard `logging` module under the `app_config` logger. Messages describe problems but never include config values.

## Development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ruff check . && pytest
```

CI runs lint, tests and a CLI smoke check on Python 3.10–3.13 (`.github/workflows/ci.yml`).
