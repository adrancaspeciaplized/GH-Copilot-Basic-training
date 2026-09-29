"""Exception hierarchy for configuration loading."""


class ConfigError(Exception):
    """Base class for all configuration errors."""


class ConfigFileNotFoundError(ConfigError):
    """The configuration file does not exist or cannot be read."""


class ConfigFormatError(ConfigError):
    """The configuration file is not valid JSON or not a JSON object."""


class ConfigValidationError(ConfigError):
    """The configuration is valid JSON but its fields are missing or invalid."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("Invalid configuration: " + "; ".join(errors))
