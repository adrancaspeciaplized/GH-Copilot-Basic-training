import json
import logging

import pytest

from app_config import (
    Config,
    ConfigError,
    ConfigFileNotFoundError,
    ConfigFormatError,
    ConfigValidationError,
    load_config,
    parse_config,
)
from app_config.__main__ import main

VALID = {"port": 8080, "host": "localhost", "enable_logging": True}


def write_json(tmp_path, data, name="config.json"):
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_valid_config(tmp_path):
    config = load_config(write_json(tmp_path, VALID))
    assert config == Config(port=8080, host="localhost", enable_logging=True)


def test_extra_fields_are_ignored(tmp_path):
    config = load_config(write_json(tmp_path, {**VALID, "extra": 1}))
    assert config.port == 8080


def test_missing_file_raises(tmp_path):
    with pytest.raises(ConfigFileNotFoundError):
        load_config(tmp_path / "missing.json")


def test_errors_share_base_class(tmp_path):
    with pytest.raises(ConfigError):
        load_config(tmp_path / "missing.json")


@pytest.mark.parametrize("text", ["", "{", "{'port': 1}", "not json"])
def test_malformed_json_raises_format_error(text):
    with pytest.raises(ConfigFormatError):
        parse_config(text)


@pytest.mark.parametrize("text", ["[]", "42", '"text"', "null"])
def test_non_object_root_raises_format_error(text):
    with pytest.raises(ConfigFormatError, match="must be a JSON object"):
        parse_config(text)


@pytest.mark.parametrize("field", ["port", "host", "enable_logging"])
def test_missing_required_field(field):
    data = {k: v for k, v in VALID.items() if k != field}
    with pytest.raises(ConfigValidationError, match=f"'{field}' is required"):
        parse_config(json.dumps(data))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("port", "8080", "must be an integer"),
        ("port", 80.5, "must be an integer"),
        ("port", True, "must be an integer"),
        ("port", None, "must be an integer"),
        ("port", 0, "between 1 and 65535"),
        ("port", 65536, "between 1 and 65535"),
        ("host", 123, "must be a string"),
        ("host", "", "must not be empty"),
        ("host", "   ", "must not be empty"),
        ("enable_logging", "true", "must be a boolean"),
        ("enable_logging", 1, "must be a boolean"),
    ],
)
def test_invalid_field_values(field, value, message):
    with pytest.raises(ConfigValidationError, match=message):
        parse_config(json.dumps({**VALID, field: value}))


@pytest.mark.parametrize("port", [1, 65535])
def test_port_boundaries_are_valid(port):
    assert parse_config(json.dumps({**VALID, "port": port})).port == port


def test_all_validation_errors_are_reported_together():
    with pytest.raises(ConfigValidationError) as exc_info:
        parse_config("{}")
    assert len(exc_info.value.errors) == 3


def test_success_is_logged(tmp_path, caplog):
    with caplog.at_level(logging.INFO, logger="app_config"):
        load_config(write_json(tmp_path, VALID))
    assert "Configuration loaded" in caplog.text


def test_validation_failure_is_logged_without_values(caplog):
    secret_host = "super-secret-host.internal"
    with (
        caplog.at_level(logging.ERROR, logger="app_config"),
        pytest.raises(ConfigValidationError),
    ):
        parse_config(json.dumps({"host": secret_host, "port": "bad"}))
    assert "validation failed" in caplog.text
    assert secret_host not in caplog.text


def test_cli_success(tmp_path, capsys):
    assert main([str(write_json(tmp_path, VALID))]) == 0
    assert "OK" in capsys.readouterr().out


def test_cli_failure(tmp_path, capsys):
    assert main([str(tmp_path / "missing.json")]) == 1
    assert "error:" in capsys.readouterr().err
