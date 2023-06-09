import logging
import sys
from logging import Logger
from typing import TYPE_CHECKING, Any, Final

import click

import app
from app.lib import ConfigurationError

from .utils.config_file_loaders import (
    CONFIG_FORMATS,
    LoadConfigError,
    load_config_file,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


# =============================================================================
# CONSTANTS
# =============================================================================

_LOGGER: Final[Logger] = logging.getLogger("app.runtime")


# =============================================================================
# HELPERS
# =============================================================================


def _configure_runtime(
    config: str,
    config_format: CONFIG_FORMATS,
    log_level: str,
    verbosity: int,
) -> None:
    from .setup import setup
    from .utils.printers import print_error

    try:
        app.registry_v1.set("config_format", config_format)
        app.registry_v1.set("verbosity", verbosity)

        config_contents: Mapping[str, Any] | None = (
            load_config_file(
                config_file_path=config,
                config_format=config_format,
            )
            if config is not None
            else None
        )
        app.setup = setup
        app.setup(settings=config_contents, log_level=log_level)
    except LoadConfigError as exp:
        _default_err: str = "Error loading configuration."
        print_error(error_message=exp.message or _default_err, exception=exp)
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
            'error was: "{}".'.format(str(exp))
        )
        # This might not be logged as logging may still be un-configured when
        # this error occurs.
        _LOGGER.exception(_err_msg)
        print_error(error_message=_err_msg, exception=exp)
        sys.exit(4)


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
    help=(
        "Set the location of the configuration file to use. Both toml and "
        "yaml file formats are supported."
    ),
    type=click.Path(exists=True, readable=True, resolve_path=True),
)
@click.option(
    "--config-format",
    default="auto",
    envvar="IDR_CLIENT_CONFIG_FORMAT",
    help=(
        "The config format of the configuration file in use. Both toml and "
        "yaml configuration formats are supported. 'auto' determines the "
        "configuration file in use based on the extension of the file and "
        "when that fails, defaults to assuming the configuration file is a "
        "toml file."
    ),
    show_default=True,
    type=click.Choice(choices=("auto", "toml", "yaml")),
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
            "ERROR",
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
    help=(
        "Set the level of output to expect from the program on stdout. This "
        "is different from log level."
    ),
)
@click.version_option(package_name="idr-client", message="%(version)s")
def main(
    config: str | None,
    config_format: CONFIG_FORMATS,
    log_level: str,
    verbosity: int,
) -> None:
    _configure_runtime(
        config=config,
        config_format=config_format,
        log_level=log_level,
        verbosity=verbosity,
    )

    from .utils.printers import print_error, print_success

    try:
        # Delay this import as late as possible to avoid cyclic imports,
        # especially before configuration has been loaded.
        from .usecases import start

        start()
        print_success("Done 😁")
    except Exception as exp:  # noqa: BLE001
        _err_msg: str = (
            "An unhandled error occurred at runtime. The cause of the error "
            'was: "{}".'.format(str(exp))
        )
        _LOGGER.exception(_err_msg)
        print_error(error_message=_err_msg, exception=exp)
        sys.exit(5)


if __name__ == "__main__":  # pragma: no cover
    main(auto_envvar_prefix="IDR_CLIENT")
