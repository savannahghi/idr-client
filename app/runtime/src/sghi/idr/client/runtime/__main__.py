import logging
import sys
from logging import Logger
from typing import TYPE_CHECKING, Any, Final, Literal

import click
import sghi.idr.client.core as app
from sghi.idr.client.core.lib import ConfigurationError

from .constants import APP_DISPATCHER_REG_KEY, APP_VERBOSITY_REG_KEY
from .ui import UI, NoUI
from .utils import dispatch
from .utils.config_file_loaders import (
    CONFIG_FORMATS,
    LoadConfigError,
    load_config_file,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


# =============================================================================
# TYPES
# =============================================================================

Supported_UIs = Literal["none", "simple", "rich"]


# =============================================================================
# CONSTANTS
# =============================================================================

_LOGGER: Final[Logger] = logging.getLogger("sghi.idr.client.runtime")


# =============================================================================
# HELPERS
# =============================================================================


def _configure_runtime(
    app_dispatcher: dispatch.Dispatcher,
    config: str | None,
    config_format: CONFIG_FORMATS,
    log_level: str,
    verbosity: int,
) -> None:
    from .setup import setup

    try:
        app.registry.set(APP_VERBOSITY_REG_KEY, verbosity)

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
        app_dispatcher.send(
            dispatch.ConfigErrorSignal(exp.message or _default_err, exp),
        )
        sys.exit(2)
    except ConfigurationError as exp:
        _err_msg: str = (
            "Error configuring the runtime. The cause of the error was: "
            "{}".format(exp.message)
        )
        # This might not be logged as logging may still be un-configured when
        # this error occurs.
        _LOGGER.exception(_err_msg)
        app_dispatcher.send(dispatch.ConfigErrorSignal(_err_msg, exp))
        sys.exit(3)
    except Exception as exp:  # noqa: BLE001
        _err_msg: str = (
            "An unknown error occurred during runtime setup. The cause of the "
            "error was: {}".format(str(exp))
        )
        # This might not be logged as logging may still be un-configured when
        # this error occurs.
        _LOGGER.exception(_err_msg)
        app_dispatcher.send(dispatch.ConfigErrorSignal(_err_msg, exp))
        sys.exit(4)


def _set_ui(preferred_ui: Supported_UIs) -> UI:
    match preferred_ui:
        case "none":
            return NoUI()
        case "simple":
            from sghi.idr.client.runtime.tui.simple import SimpleUI

            return SimpleUI()
        case "rich":
            from sghi.idr.client.runtime.tui.rich import RichUI

            return RichUI()
        case _:
            _err_msg: str = "Unsupported UI option given."
            raise ConfigurationError(message=_err_msg)


# =============================================================================
# MAIN
# =============================================================================


@click.command(
    epilog="Lets do this! ;)",
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
    "--ui",
    default="none",
    envvar="IDR_CLIENT_UI",
    help="Select a user interface to use.",
    show_default=True,
    type=click.Choice(
        choices=("none", "simple", "rich"),
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
    ui: Supported_UIs,
    verbosity: int,
) -> None:
    """
    An ETL tool that draws/extracts data from data sources, transforms
    and/or cleans the data and then drains/uploads the cleaned data to a data
    sink.

    \f

    :param config: An option path to a configuration file.
    :param config_format: The format of the config contents. Can be auto which
        allows the configuration format to be determined from the extension of
        the file name.
    :param log_level: The log level of the "root application" logger.
    :param ui: The preferred user interface to use.
    :param verbosity: The level of output to expect from the application on
        stdout. This is different from log level.

    :return: None.
    """
    app_dispatcher: dispatch.Dispatcher = dispatch.Dispatcher()
    app.registry.set(APP_DISPATCHER_REG_KEY, app_dispatcher)

    _set_ui(preferred_ui=ui).start()

    _configure_runtime(
        app_dispatcher=app_dispatcher,
        config=config,
        config_format=config_format,
        log_level=log_level,
        verbosity=verbosity,
    )

    try:
        # Delay this import as late as possible to avoid cyclic imports,
        # especially before configuration has been loaded.
        from .usecases import start

        app_dispatcher.send(dispatch.AppPreStartSignal())
        start()
        app_dispatcher.send(dispatch.AppPreStopSignal())
    except Exception as exp:  # noqa: BLE001
        _err_msg: str = (
            "An unhandled error occurred at runtime. The cause of the error "
            "was: {}.".format(str(exp))
        )
        _LOGGER.exception(_err_msg)
        app_dispatcher.send(
            dispatch.UnhandledRuntimeErrorSignal(_err_msg, exp),
        )
        sys.exit(5)


if __name__ == "__main__":  # pragma: no cover
    main(auto_envvar_prefix="IDR_CLIENT")
