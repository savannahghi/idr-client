import inspect
from logging.config import dictConfig
from typing import Any, Dict, List, Mapping, Optional, Sequence, Type, cast

import yaml
from yaml import Loader

from app.core import DataSourceType
from app.lib import (
    AppRegistry,
    Config,
    ImproperlyConfiguredError,
    SettingInitializer,
    import_string,
)

# =============================================================================
# CONSTANTS
# =============================================================================

_LOGGING_CONFIG_KEY = "LOGGING"

_SUPPORTED_DATA_SOURCE_TYPES_CONFIG_KEY = "SUPPORTED_DATA_SOURCE_TYPES"

_DEFAULT_CONFIG: Dict[str, Any] = {
    _LOGGING_CONFIG_KEY: {
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
    },
    _SUPPORTED_DATA_SOURCE_TYPES_CONFIG_KEY: [
        "app.imp.sql_data.SQLDataSourceType"
    ],
}


# =============================================================================
# APP GLOBALS
# =============================================================================

registry: AppRegistry = None  # type: ignore
"""
The application registry. Provides lookup for important resources and services
within the application. This value is only available after a successful
application set up. That is, after ``app.setup()`` completes successfully.
"""

settings: Config = None  # type: ignore
"""
The application configurations. This value is only available after a
successful application set up. That is, after ``app.setup()`` completes
successfully.
"""


# =============================================================================
# HELPERS
# =============================================================================


def _load_config_file(config_file_path: str) -> Mapping[str, Any]:
    # TODO: Ensure that a valid config file path was given and if not raise an
    #  appropriate Exception.
    with open(config_file_path, "rb") as config_file:
        return yaml.load(config_file, Loader=Loader)


# =============================================================================
# DEFAULT SETTINGS INITIALIZERS
# =============================================================================


class _LoggingInitializer(SettingInitializer):
    """A :class:`SettingInitializer` that configures logging for the app."""

    @property
    def setting(self) -> str:
        return _LOGGING_CONFIG_KEY

    def execute(self, an_input: Optional[Mapping[str, Any]]) -> Any:
        logging_config: Dict[str, Any] = dict(
            an_input or _DEFAULT_CONFIG[self.setting]
        )
        dictConfig(logging_config)
        return logging_config


class _SupportedDataSourceTypesInitializer(SettingInitializer):
    """
    A :class:`SettingInitializer` that initializes and registers supported
    data types in the app registry.
    """

    @property
    def setting(self) -> str:
        return _SUPPORTED_DATA_SOURCE_TYPES_CONFIG_KEY

    def execute(self, an_input: Optional[Sequence[str]]) -> Any:
        supported_dst: Sequence[str] = (
            an_input or _DEFAULT_CONFIG[self.setting]
        )
        global registry
        _dst: DataSourceType
        registry.data_source_types = {
            _dst.code: _dst
            for _dst in map(
                lambda _s: self._dotted_path_to_data_source_type_klass(_s)(),
                supported_dst,
            )
        }
        return supported_dst

    @staticmethod
    def _dotted_path_to_data_source_type_klass(
        dotted_path: str,
    ) -> Type[DataSourceType]:
        try:
            _module = import_string(dotted_path)
        except ImportError as exp:
            raise ImproperlyConfiguredError(
                message='"%s" does not seem to be a valid path.' % dotted_path
            ) from exp

        if not inspect.isclass(_module) or not issubclass(
            _module, DataSourceType
        ):  # type: ignore
            raise ImproperlyConfiguredError(
                message=(
                    'Invalid value, "%s" is either not class or is not a '
                    'subclass of "app.core.DataSourceType".' % dotted_path
                )
            )
        return cast(Type[DataSourceType], _module)


# =============================================================================
# APP SETUP FUNCTION
# =============================================================================


def setup(
    initial_settings: Optional[Mapping[str, Any]] = None,
    settings_initializers: Optional[Sequence[SettingInitializer]] = None,
    config_file_path: Optional[str] = None,
) -> None:
    """
    Set up the application and ready it for use.

    :param initial_settings: Optional configuration parameters to override the
        defaults.
    :param settings_initializers:
    :param config_file_path:

    :return: None.
    """
    # Start by setting up the application registry
    global registry
    registry = AppRegistry()

    # Load the application settings
    _settings_dict: Dict[str, Any] = dict(initial_settings or _DEFAULT_CONFIG)
    if config_file_path:  # load config from a file when provided
        _settings_dict.update(_load_config_file(config_file_path))

    # Load initializers
    _initializers: List[Any] = list(settings_initializers or [])
    _initializers.insert(0, _LoggingInitializer())
    _initializers.insert(1, _SupportedDataSourceTypesInitializer())

    global settings
    settings = Config(
        settings=_settings_dict, settings_initializers=_initializers
    )
