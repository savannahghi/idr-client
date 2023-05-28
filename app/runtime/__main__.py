import sys
from collections.abc import Mapping, Sequence
from logging.config import dictConfig
from typing import Any, Final

import click
import yaml
from toolz import pipe
from toolz.curried import map

import app
from app.lib import (
    Config,
    ImproperlyConfiguredError,
    SettingInitializer,
    import_string_as_klass,
)

# =============================================================================
# CONSTANTS
# =============================================================================

_ETL_PROTOCOLS_CONFIG_KEY: Final[str] = "ETL_PROTOCOLS"

_LOGGING_CONFIG_KEY: Final[str] = "LOGGING"

_SETTINGS_INITIALIZERS_CONFIG_KEY: Final[str] = "SETTINGS_INITIALIZERS"

_DEFAULT_CONFIG: Final[dict[str, Any]] = {
    _ETL_PROTOCOLS_CONFIG_KEY: [],
    _LOGGING_CONFIG_KEY: {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "%(asctime)s %(levelname)s %(name)s - %(message)s",
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
}


# =============================================================================
# HELPERS
# =============================================================================


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
            return initializer_klass()
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

    return pipe(
        initializers_dotted_paths,
        map(_dotted_path_to_initializer_instance),
        list,
    )


def load_yaml_config_file(config_file_path: str) -> Mapping[str, Any]:
    with open(config_file_path, "rb") as config_file:
        try:
            config_content: Mapping[str, Any] = yaml.safe_load(config_file)
        except Exception as exp:  # noqa
            click.echo(
                click.style(
                    "Error opening the given configuration file. Please "
                    "ensure that the configuration file contents consist of "
                    'valid yaml. The cause of the error was: "{}"'.format(exp),
                    fg="red",
                ),
                file=sys.stderr,
            )
            sys.exit()
        return config_content


# =============================================================================
# DEFAULT SETTINGS INITIALIZERS
# =============================================================================
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


# =============================================================================
# APP SETUP FUNCTION
# =============================================================================


def setup(
    settings: Mapping[str, Any] | None = None,
    settings_initializers: Sequence[SettingInitializer] | None = None,
) -> None:
    settings_dict: dict[str, Any] = dict(_DEFAULT_CONFIG)
    settings_dict.update(settings)
    initializers: list[SettingInitializer] = list(settings_initializers or [])
    initializers.extend(
        load_settings_initializers(
            settings_dict.get(_SETTINGS_INITIALIZERS_CONFIG_KEY, ()),
        ),
    )

    initializers.insert(0, _LoggingInitializer())
    app.settings = Config(  # type: ignore
        settings=settings_dict,
        settings_initializers=initializers,
    )


# =============================================================================
# MAIN
# =============================================================================


@click.command()
def main() -> None:
    config_contents: Mapping[str, Any] = load_yaml_config_file("config.yaml")
    app.setup = setup
    app.setup(settings=config_contents)
    click.echo(click.style("Done ...", fg="green"))


if __name__ == "__main__":  # pragma: no cover
    main()
