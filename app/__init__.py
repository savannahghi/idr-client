from collections.abc import Mapping, Sequence
from logging.config import dictConfig
from typing import Any, Final, cast

import yaml

from app.core import DataSourceType
from app.lib import (
    AppRegistry,
    Config,
    DefaultTransportFactory,
    ImproperlyConfiguredError,
    SettingInitializer,
    import_string,
    import_string_as_klass,
)

# =============================================================================
# CONSTANTS
# =============================================================================

_DEFAULT_TRANSPORT_FACTORY_CONFIG_KEY: Final[str] = "DEFAULT_TRANSPORT_FACTORY"

_LOGGING_CONFIG_KEY: Final[str] = "LOGGING"

_SETTINGS_INITIALIZERS_CONFIG_KEY: Final[str] = "SETTINGS_INITIALIZERS"

_SUPPORTED_DATA_SOURCE_TYPES_CONFIG_KEY: Final[
    str
] = "SUPPORTED_DATA_SOURCE_TYPES"

_DEFAULT_CONFIG: Final[dict[str, Any]] = {
    _LOGGING_CONFIG_KEY: {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": (
                    "%(levelname)s: %(asctime)s %(module)s "
                    "%(process)d %(message)s"
                ),
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
        },
        "loggers": {
            "app": {"level": "INFO", "handlers": ["console"]},
        },
    },
    _SETTINGS_INITIALIZERS_CONFIG_KEY: [],
    _SUPPORTED_DATA_SOURCE_TYPES_CONFIG_KEY: [],
}


# =============================================================================
# APP GLOBALS
# =============================================================================

registry: Final[AppRegistry] = None  # type: ignore
"""
The application registry. Provides lookup for important resources and services
within the application. This value is only available after a successful
application set up. That is, after ``app.setup()`` completes successfully.
"""

settings: Final[Config] = None  # type: ignore
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
        return yaml.safe_load(config_file)


def _load_settings_initializers(
    initializers_dotted_paths: Sequence[str],
) -> Sequence[SettingInitializer]:
    initializers: list[SettingInitializer] = []
    for _initializer_dotted_path in initializers_dotted_paths:
        try:
            initializer_klass: type[SettingInitializer]
            initializer_klass = import_string_as_klass(
                _initializer_dotted_path,
                SettingInitializer,
            )
            initializers.append(initializer_klass())  # type: ignore
        except ImportError as exp:
            raise ImproperlyConfiguredError(
                message='"%s" does not seem to be a valid path.'
                % _initializer_dotted_path,
            ) from exp
        except TypeError as exp:
            raise ImproperlyConfiguredError(
                message=(
                    'Invalid value, "%s" is either not class or is not a '
                    'subclass of "app.lib.SettingInitializer".'
                    % _initializer_dotted_path
                ),
            ) from exp

    return initializers


# =============================================================================
# DEFAULT SETTINGS INITIALIZERS
# =============================================================================


class _DefaultTransportFactoryInitializer(SettingInitializer):
    @property
    def setting(self) -> str:
        return _DEFAULT_TRANSPORT_FACTORY_CONFIG_KEY

    def execute(self, an_input: str | None) -> str | None:
        # If the default transport setting has not been provided or is empty,
        # do nothing.
        if not an_input:
            return an_input

        if type(an_input) is not str:
            raise ImproperlyConfiguredError(
                message='The value of the "%s" setting must be a string'
                % _DEFAULT_TRANSPORT_FACTORY_CONFIG_KEY,
            )

        default_transport_factory: DefaultTransportFactory
        try:
            default_transport_factory = cast(
                DefaultTransportFactory,
                import_string(an_input),
            )
            global registry
            registry.default_transport_factory = default_transport_factory
        except (ImportError, TypeError) as exp:
            raise ImproperlyConfiguredError(
                message="Unable to import the default transport factory at "
                '"%s". Ensure a valid path was given.' % an_input,
            ) from exp

        return an_input


class _LoggingInitializer(SettingInitializer):
    """A :class:`SettingInitializer` that configures logging for the app."""

    @property
    def setting(self) -> str:
        return _LOGGING_CONFIG_KEY

    def execute(self, an_input: Mapping[str, Any] | None) -> Mapping[str, Any]:
        logging_config: dict[str, Any] = dict(
            an_input or _DEFAULT_CONFIG[self.setting],
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

    def execute(self, an_input: Sequence[str] | None) -> Sequence[str]:
        supported_dst: Sequence[str] = (
            an_input or _DEFAULT_CONFIG[self.setting]
        )
        global registry
        _dst: DataSourceType
        registry.data_source_types = {
            _dst.code: _dst
            for _dst in (
                self._dotted_path_to_data_source_type_klass(_s)()
                for _s in supported_dst
            )
        }
        return supported_dst

    @staticmethod
    def _dotted_path_to_data_source_type_klass(
        dotted_path: str,
    ) -> type[DataSourceType]:
        try:
            data_source_type_klass: type[DataSourceType]
            data_source_type_klass = import_string_as_klass(
                dotted_path,
                DataSourceType,
            )
            return data_source_type_klass
        except ImportError as exp:
            _msg: str = '"%s" does not seem to be a valid path.' % dotted_path
            raise ImproperlyConfiguredError(message=_msg) from exp
        except TypeError as exp:
            _msg: str = (
                'Invalid value, "%s" is either not class or is not a subclass '
                'of "app.core.DataSourceType".' % dotted_path
            )
            raise ImproperlyConfiguredError(message=_msg) from exp


# =============================================================================
# APP SETUP FUNCTION
# =============================================================================


def setup(
    initial_settings: Mapping[str, Any] | None = None,
    settings_initializers: Sequence[SettingInitializer] | None = None,
    config_file_path: str | None = None,
) -> None:
    """
    Set up the application and ready it for use.

    This involves configuring the settings and app registry, configuring
    logging, loading supported
    :class:`data source types <app.core.DataSourceType>` and initializing the
    default :class:`transport <app.core.Transport>`.

    :param initial_settings: Optional configuration parameters to override the
        defaults.
    :param settings_initializers:
    :param config_file_path:

    :return: None.
    """
    # Start by setting up the application registry
    global registry
    registry = AppRegistry()  # type: ignore

    # Load the application settings
    _settings_dict: dict[str, Any] = dict(initial_settings or _DEFAULT_CONFIG)
    # Load config from a file when provided
    if config_file_path:  # pragma: no branch
        _settings_dict.update(_load_config_file(config_file_path))

    # Load initializers
    _initializers: list[Any] = list(settings_initializers or [])
    _initializers.extend(
        _load_settings_initializers(
            _settings_dict.get(_SETTINGS_INITIALIZERS_CONFIG_KEY, ()),
        ),
    )
    # FIXME: This is hardcoded default behaviour and it's problematic to test
    #  or mock properly.
    _initializers.insert(0, _LoggingInitializer())
    _initializers.insert(1, _SupportedDataSourceTypesInitializer())
    _initializers.insert(2, _DefaultTransportFactoryInitializer())

    global settings
    settings = Config(  # type: ignore
        settings=_settings_dict,
        settings_initializers=_initializers,
    )
