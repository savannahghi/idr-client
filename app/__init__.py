from logging.config import dictConfig
from typing import Any, Dict, List, Mapping, Optional, Sequence, Type

import yaml
from yaml import Loader

from app.core import DataSourceType
from app.lib import (
    AppRegistry,
    Config,
    ImproperlyConfiguredError,
    SettingInitializer,
    import_string_as_klass,
)

# =============================================================================
# CONSTANTS
# =============================================================================

_LOGGING_CONFIG_KEY = "LOGGING"

_SETTINGS_INITIALIZERS_CONFIG_KEY = "SETTINGS_INITIALIZERS"

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
    _SETTINGS_INITIALIZERS_CONFIG_KEY: [],
    _SUPPORTED_DATA_SOURCE_TYPES_CONFIG_KEY: [],
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


def _load_config_file(
    config_file_path: str,
) -> Mapping[str, Any]:  # pragma: no cover
    # TODO: Ensure that a valid config file path was given and if not raise an
    #  appropriate Exception.
    with open(config_file_path, "rb") as config_file:
        return yaml.load(config_file, Loader=Loader)


def _load_settings_initializers(
    initializers_dotted_paths: Sequence[str],
) -> Sequence[SettingInitializer]:
    initializers: List[SettingInitializer] = list()
    for _initializer_dotted_path in initializers_dotted_paths:
        try:
            initializer_klass: Type[SettingInitializer]
            initializer_klass = import_string_as_klass(
                _initializer_dotted_path, SettingInitializer
            )
            initializers.append(initializer_klass())
        except ImportError as exp:
            raise ImproperlyConfiguredError(
                message='"%s" does not seem to be a valid path.'
                % _initializer_dotted_path
            ) from exp
        except TypeError as exp:
            raise ImproperlyConfiguredError(
                message=(
                    'Invalid value, "%s" is either not class or is not a '
                    'subclass of "app.lib.SettingInitializer".'
                    % _initializer_dotted_path
                )
            ) from exp

    return initializers


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
            data_source_type_klass: Type[DataSourceType]
            data_source_type_klass = import_string_as_klass(
                dotted_path, DataSourceType
            )
            return data_source_type_klass
        except ImportError as exp:
            raise ImproperlyConfiguredError(
                message='"%s" does not seem to be a valid path.' % dotted_path
            ) from exp
        except TypeError as exp:
            raise ImproperlyConfiguredError(
                message=(
                    'Invalid value, "%s" is either not class or is not a '
                    'subclass of "app.core.DataSourceType".' % dotted_path
                )
            ) from exp


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
    # Load config from a file when provided
    if config_file_path:  # pragma: no branch
        _settings_dict.update(_load_config_file(config_file_path))

    # Load initializers
    _initializers: List[Any] = list(settings_initializers or [])
    _initializers.extend(
        _load_settings_initializers(
            _settings_dict.get(_SETTINGS_INITIALIZERS_CONFIG_KEY, tuple())
        )
    )
    _initializers.insert(0, _LoggingInitializer())
    _initializers.insert(1, _SupportedDataSourceTypesInitializer())

    global settings
    settings = Config(
        settings=_settings_dict, settings_initializers=_initializers
    )
