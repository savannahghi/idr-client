import os
from collections.abc import Mapping
from typing import Any

from app.lib import ConfigurationError

# =============================================================================
# Exceptions
# =============================================================================


class LoadConfigError(ConfigurationError):
    """Error while loading the configuration from a file."""


# =============================================================================
# LOADERS
# =============================================================================


def load_config_file(config_file_path: str) -> Mapping[str, Any]:
    _, file_ext = os.path.splitext(config_file_path)
    match file_ext:
        case ".yaml" | ".yml":
            return load_yaml_config_file(config_file_path)
        case _:
            return load_toml_config_file(config_file_path)


def load_toml_config_file(config_file_path: str) -> Mapping[str, Any]:
    import tomllib

    try:
        with open(config_file_path, "rb") as config_file:
            config_content: Mapping[str, Any] = tomllib.load(config_file)
    except Exception as exp:  # noqa: BLE001
        _err_msg: str = (
            "Error opening the given configuration file. Please ensure that "
            "the configuration file contents consist of valid toml, and that "
            '"{}" points to an existing readable file. The cause of the error '
            'was: "{}"'.format(config_file_path, exp)
        )
        raise LoadConfigError(message=_err_msg) from exp
    return config_content


def load_yaml_config_file(config_file_path: str) -> Mapping[str, Any]:
    import yaml

    try:
        with open(config_file_path, "rb") as config_file:
            config_content: Mapping[str, Any] = yaml.safe_load(config_file)
    except Exception as exp:  # noqa: BLE001
        _err_msg: str = (
            "Error opening the given configuration file. Please ensure that "
            "the configuration file contents consist of valid yaml, and that "
            '"{}" points to an existing readable file. The cause of the error '
            'was: "{}"'.format(config_file_path, exp)
        )
        raise LoadConfigError(message=_err_msg) from exp
    return config_content
