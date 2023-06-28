import os
from collections.abc import Mapping
from typing import Any, Final, Literal

from jinja2 import StrictUndefined, Template, select_autoescape
from jinja2.exceptions import UndefinedError
from jinja2.sandbox import ImmutableSandboxedEnvironment as Environment
from sghi.idr.client.core.lib import ConfigurationError

# =============================================================================
# TYPES
# =============================================================================

CONFIG_FORMATS = Literal["auto", "toml", "yaml"]

# =============================================================================
# CONSTANTS
# =============================================================================

_CONFIG_JINJA_ENV: Final[Environment] = Environment(
    autoescape=select_autoescape(default=True, default_for_string=True),
    undefined=StrictUndefined,
)


# =============================================================================
# EXCEPTIONS
# =============================================================================


class LoadConfigError(ConfigurationError):
    """Error while loading the configuration from a file."""


# =============================================================================
# HELPERS
# =============================================================================


def _auto_detect_config_format_and_load_config(
    config_file_path: str,
) -> Mapping[str, Any]:
    _, file_ext = os.path.splitext(config_file_path)
    match file_ext:
        case ".yaml" | ".yml":
            return load_yaml_config_file(config_file_path)
        case _:
            return load_toml_config_file(config_file_path)


def _read_config(config_file_path: str) -> str:
    with open(config_file_path) as config_file:
        config_content: str = config_file.read()

    return config_content


def _substitute_env_variables(config_content: str) -> str:
    config_template: Template = _CONFIG_JINJA_ENV.from_string(config_content)
    try:
        return config_template.render(os.environ)
    except UndefinedError as exp:
        _err_message: str = f"Undefined environment variable used. {str(exp)}."
        raise LoadConfigError(message=_err_message) from exp


# =============================================================================
# LOADERS
# =============================================================================


def load_config_file(
    config_file_path: str,
    config_format: CONFIG_FORMATS = "auto",
) -> Mapping[str, Any]:
    match config_format:
        case "auto":
            return _auto_detect_config_format_and_load_config(
                config_file_path=config_file_path,
            )
        case "toml":
            return load_toml_config_file(config_file_path)
        case "yaml":
            return load_yaml_config_file(config_file_path)
        case _:
            _err_msg: str = "Unknown config format given."
            raise LoadConfigError(message=_err_msg)


def load_toml_config_file(config_file_path: str) -> Mapping[str, Any]:
    import tomllib

    try:
        config_src: str = _substitute_env_variables(
            config_content=_read_config(config_file_path),
        )
        config_content: Mapping[str, Any] = tomllib.loads(config_src)
    except LoadConfigError:
        raise
    except Exception as exp:  # noqa: BLE001
        _err_msg: str = (
            "Error opening/reading the given configuration file. Please "
            "ensure that the configuration file contents consist of valid "
            'toml, and that "{}" points to an existing readable file. The '
            'cause of the error was: "{}"'.format(config_file_path, exp)
        )
        raise LoadConfigError(message=_err_msg) from exp
    return config_content


def load_yaml_config_file(config_file_path: str) -> Mapping[str, Any]:
    import yaml

    try:
        config_src: str = _substitute_env_variables(
            config_content=_read_config(config_file_path),
        )
        config_content: Mapping[str, Any] = yaml.safe_load(config_src)
    except LoadConfigError:
        raise
    except Exception as exp:  # noqa: BLE001
        _err_msg: str = (
            "Error opening/reading the given configuration file. Please "
            "ensure that the configuration file contents consist of valid "
            'yaml, and that "{}" points to an existing readable file. The '
            'cause of the error was: "{}"'.format(config_file_path, exp)
        )
        raise LoadConfigError(message=_err_msg) from exp
    return config_content
