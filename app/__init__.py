from logging.config import dictConfig
from typing import Any, Dict, Mapping, Optional

import yaml
from yaml import Loader

from app.core import Task
from app.lib import Config, SettingInitializer

# =============================================================================
# CONSTANTS
# =============================================================================

_DEFAULT_CONFIG: Dict[str, Any] = {
    "logging": {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": (
                    "%(levelname)s: %(asctime)s %(module)s "
                    "%(process)d %(thread)d %(message)s"
                )
            }
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            }
        },
        "root": {"level": "INFO", "handlers": ["console"]},
    }
}


settings: Config = None  # type: ignore


# =============================================================================
# HELPERS
# =============================================================================

def _load_config_file(config_file_path: str) -> Mapping[str, Any]:
    with open(config_file_path, "rb") as config_file:
        return yaml.load(config_file, Loader=Loader)


class _LoggingInitializer(Task[Any, Any]):
    """A ``SettingInitializer`` that configures logging for the app."""

    def execute(self, an_input: Optional[Mapping[str, Any]]) -> Any:
        logging_config: Dict[str, Any] = dict(
            an_input or _DEFAULT_CONFIG["logging"]
        )
        dictConfig(logging_config)
        return logging_config


# =============================================================================
# APP SETUP FUNCTION
# =============================================================================

def setup(
        initial_settings: Optional[Mapping[str, Any]] = None,
        settings_initializers: Optional[Mapping[str, SettingInitializer]] = None,  # noqa
        config_file_path: Optional[str] = None
) -> None:
    """
    Set up the application and ready it for use.

    :param initial_settings: Optional configuration parameters to override the
        defaults.
    :param settings_initializers:
    :param config_file_path:

    :return: None.
    """
    _settings_dict: Dict[str, Any] = dict(initial_settings or _DEFAULT_CONFIG)
    if config_file_path:  # load config from a file when provided
        _settings_dict.update(_load_config_file(config_file_path))
    _initializers_dict: Dict[str, Any] = dict(settings_initializers or {})
    _initializers_dict.update({
        "logging": _LoggingInitializer()
    })

    global settings
    settings = Config(
        settings=_settings_dict,
        settings_initializers=_initializers_dict
    )
