import builtins
import logging
import sys
import traceback
from collections.abc import Callable, Mapping, Sequence
from logging import Logger
from logging.config import dictConfig
from typing import Any, Final, cast

import click
import yaml
from toolz import pipe
from toolz.curried import groupby, map

import app
from app.core_v1.domain import ETLProtocol
from app.lib import (
    Config,
    ConfigurationError,
    ImproperlyConfiguredError,
    SettingInitializer,
    import_string,
    import_string_as_klass,
)

# =============================================================================
# TYPES
# =============================================================================

_ETLProtocol_Factory = Callable[[], ETLProtocol]


# =============================================================================
# CONSTANTS
# =============================================================================

_ETL_PROTOCOLS_CONFIG_KEY: Final[str] = "ETL_PROTOCOLS"

_LOGGER: Final[Logger] = logging.getLogger("app.runtime.main")

_LOGGING_CONFIG_KEY: Final[str] = "LOGGING"

_SETTINGS_INITIALIZERS_CONFIG_KEY: Final[str] = "SETTINGS_INITIALIZERS"

_DEFAULT_CONFIG: Final[dict[str, Any]] = {
    _ETL_PROTOCOLS_CONFIG_KEY: [],
    _LOGGING_CONFIG_KEY: {
        "version": 1,
        "formatters": {
            "simple": {
                "format": "%(asctime)s %(levelname)s %(name)s - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "level": "DEBUG",
            },
        },
        "loggers": {
            "app": {"level": "INFO", "handlers": ["console"]},
        },
    },
    _SETTINGS_INITIALIZERS_CONFIG_KEY: [],
}


# =============================================================================
# HELPERS
# =============================================================================


def _initialize_and_load_etl_protocols(
    etl_protocol_factories: Sequence[_ETLProtocol_Factory],
) -> None:
    def _etl_protocol_factory_to_instance(
        _etl_protocol_factory: _ETLProtocol_Factory,
    ) -> ETLProtocol:
        _etl_protocol_instance: ETLProtocol = _etl_protocol_factory()
        if not isinstance(_etl_protocol_instance, ETLProtocol):
            _err_msg: str = (
                'Invalid ETLProtocol, the factory "{}.{}" returned an '
                'instance that is not a subclass of "app.core.domain.'
                'ETLProtocol".'.format(
                    _etl_protocol_factory.__module__,
                    _etl_protocol_factory.__qualname__,
                )
            )
            raise ImproperlyConfiguredError(message=_err_msg)

        return _etl_protocol_instance

    app.registry_v1.etl_protocols = cast(
        Mapping[str, ETLProtocol],
        pipe(
            etl_protocol_factories,
            map(_etl_protocol_factory_to_instance),
            groupby(lambda _ep: _ep.id),
        ),
    )


def load_settings_initializers(
    initializers_dotted_paths: Sequence[str],
) -> Sequence[SettingInitializer]:
    def _dotted_path_to_initializer_instance(
        _initializer_dotted_path: str,
    ) -> SettingInitializer:
        try:
            initializer_klass: type[SettingInitializer]
            initializer_klass = import_string_as_klass(
                _initializer_dotted_path,
                SettingInitializer,
            )
            return initializer_klass()  # type: ignore
        except ImportError as exp:
            _err_msg: str = '"{}" does not seem to be a valid path.'.format(
                _initializer_dotted_path,
            )
            raise ImproperlyConfiguredError(message=_err_msg) from exp
        except TypeError as exp:
            _err_msg: str = (
                'Invalid value, "{}" is either not class or is not a subclass '
                'of "app.lib.SettingInitializer".'.format(
                    _initializer_dotted_path,
                )
            )
            raise ImproperlyConfiguredError(message=_err_msg) from exp

    return cast(
        Sequence[SettingInitializer],
        pipe(
            initializers_dotted_paths,
            map(_dotted_path_to_initializer_instance),
            list,
        ),
    )


def load_yaml_config_file(config_file_path: str) -> Mapping[str, Any]:
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


def print_error(error_message: str, exception: BaseException | None) -> None:
    verbosity: int = app.registry_v1.get("verbosity", 0)
    click.echo(click.style(error_message, fg="red"), file=sys.stderr)
    match verbosity:
        case 1 if exception is not None:
            click.echo(
                click.style(
                    "".join(
                        traceback.format_exception(exception, chain=False),
                    ),
                    fg="magenta",
                ),
                file=sys.stderr,
            )
        case _ if verbosity > 1 and exception is not None:
            click.echo(
                click.style(
                    "".join(traceback.format_exception(exception, chain=True)),
                    fg="magenta",
                ),
                file=sys.stderr,
            )


class LoadConfigError(ConfigurationError):
    """Error while loading the configuration from a file."""


# =============================================================================
# DEFAULT SETTINGS INITIALIZERS
# =============================================================================


class _ETLProtocolInitializer(SettingInitializer):
    @property
    def setting(self) -> str:
        return _ETL_PROTOCOLS_CONFIG_KEY

    def execute(
        self,
        an_input: Sequence[str],
    ) -> Sequence[_ETLProtocol_Factory]:
        def _dotted_path_to_etl_protocol_instance(
            _etl_protocol_dotted_path: str,
        ) -> _ETLProtocol_Factory:
            try:
                _etl_protocol_factory: _ETLProtocol_Factory
                _etl_protocol_factory = import_string(  # type: ignore
                    _etl_protocol_dotted_path,
                )
                return _etl_protocol_factory
            except ImportError as exp:
                _err_msg: str = (
                    '"{}" does not seem to be a valid path.'.format(
                        _etl_protocol_dotted_path,
                    )
                )
                raise ImproperlyConfiguredError(message=_err_msg) from exp

        etl_protocols: Sequence[_ETLProtocol_Factory] = list(
            builtins.map(_dotted_path_to_etl_protocol_instance, an_input),
        )
        return etl_protocols


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
        logging.getLogger("app").setLevel(app.registry_v1.log_level)
        return logging_config


# =============================================================================
# APP SETUP FUNCTION
# =============================================================================


def setup(
    settings: Mapping[str, Any] | None = None,
    settings_initializers: Sequence[SettingInitializer] | None = None,
    log_level: int | str = "NOTSET",
    disable_default_initializers: bool = False,
) -> None:
    """Prepare the runtime and ready the application for use.

    :param settings: An optional mapping of settings and their values. When not
        provided, the runtime defaults as well as defaults set by the given
        setting initializers will be used instead.
    :param settings_initializers: An optional sequence of setting initializers
        to execute during runtime setup. Default initializers(set by the
        runtime) are always executed unless the `disable_default_initializers`
        param is set to ``True``.
    :param log_level: The log level to set for the root application logger.
        When not set defaults to the value "NOTSET".
    :param disable_default_initializers: Exclude default setting initializers
        from being executed as part of the runtime setup. The default setting
        initializers perform logging and loading of ETL protocols into the
        application registry.

    :return: None.
    """
    settings_dict: dict[str, Any] = dict(_DEFAULT_CONFIG)
    settings_dict.update(settings or {})
    initializers: list[SettingInitializer] = list(settings_initializers or [])
    initializers.extend(
        load_settings_initializers(
            settings_dict.get(_SETTINGS_INITIALIZERS_CONFIG_KEY, ()),
        ),
    )

    if not disable_default_initializers:
        initializers.insert(0, _LoggingInitializer())
        initializers.insert(1, _ETLProtocolInitializer())
    app.registry_v1.log_level = log_level
    app.settings = Config(  # type: ignore
        settings=settings_dict,
        settings_initializers=initializers,
    )
    _initialize_and_load_etl_protocols(
        app.settings.get(_ETL_PROTOCOLS_CONFIG_KEY, []),
    )


# =============================================================================
# MAIN
# =============================================================================


@click.command(
    epilog="An ETL tool that draws/extracts data from data sources, "
    "transforms and/or cleans the data and then drains/uploads the "
    "cleaned data to a data sink.",
)
@click.option(
    "-c",
    "--config",
    default=None,
    envvar="IDR_CLIENT_CONFIG",
    help="Set the location of the configuration file to use. Only yaml files "
    "are currently supported.",
    type=click.Path(exists=True, readable=True, resolve_path=True),
)
@click.option(
    "-l",
    "--log-level",
    default="WARNING",
    envvar="IDR_CLIENT_LOG_LEVEL",
    help='Set the log level of the "root application" logger.',
    show_default=True,
    type=click.Choice(
        choices=(
            "CRITICAL",
            "FATAL",
            "ERROR",
            "WARN",
            "WARNING",
            "INFO",
            "DEBUG",
            "NOTSET",
        ),
    ),
)
@click.option(
    "-v",
    "--verbose",
    "verbosity",
    count=True,
    default=0,
    envvar="IDR_CLIENT_VERBOSITY",
    help="Set the level of output to expect from the program on stdout."
    "This is different from the log level.",
)
@click.version_option(package_name="idr-client", message="%(version)s")
def main(config: str | None, log_level: str, verbosity: int) -> None:
    try:
        config_contents: Mapping[str, Any] | None = (
            load_yaml_config_file(
                config_file_path=config,
            )
            if config is not None
            else None
        )
        app.registry_v1.set("verbosity", verbosity)
        app.setup = setup
        app.setup(settings=config_contents, log_level=log_level)
    except LoadConfigError as exp:
        print_error(error_message=exp.message, exception=exp)
        sys.exit(2)
    except ConfigurationError as exp:
        _err_msg: str = (
            "Error configuring the runtime. The cause of the error was: "
            '"{}".'.format(exp.message)
        )
        # This might not be logged as logging may still be un-configured when
        # this error occurs.
        _LOGGER.exception(_err_msg)
        print_error(error_message=_err_msg, exception=exp)
        sys.exit(3)
    except Exception as exp:  # noqa: BLE001
        _err_msg: str = (
            "An unknown error occurred during runtime setup. The cause of the "
            'error was: "{}."'.format(str(exp))
        )
        # This might not be logged as logging may still be un-configured when
        # this error occurs.
        _LOGGER.exception(_err_msg)
        print_error(error_message=_err_msg, exception=exp)
        sys.exit(4)

    click.echo(click.style("Done ...", fg="green"))


if __name__ == "__main__":  # pragma: no cover
    main(auto_envvar_prefix="IDR_CLIENT")
