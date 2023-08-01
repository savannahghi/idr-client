from collections.abc import Mapping, Sequence
from typing import Any, cast

import sghi.idr.client.core as app
from sghi.idr.client.core.lib import (
    Config,
    ImproperlyConfiguredError,
    SettingInitializer,
    import_string_as_klass,
)
from toolz import pipe
from toolz.curried import map

from .constants import (
    APP_DISPATCHER_REG_KEY,
    DEFAULT_CONFIG,
    SETTINGS_INITIALIZERS_CONFIG_KEY,
)

# =============================================================================
# HELPERS
# =============================================================================


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
            'Invalid value, "{}" is either not class or is not a subclass of '
            '"app.lib.SettingInitializer".'.format(
                _initializer_dotted_path,
            )
        )
        raise ImproperlyConfiguredError(message=_err_msg) from exp


def load_settings_initializers(
    initializers_dotted_paths: Sequence[str],
) -> Sequence[SettingInitializer]:
    return cast(
        Sequence[SettingInitializer],
        pipe(
            initializers_dotted_paths,
            map(_dotted_path_to_initializer_instance),
            list,
        ),
    )


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
    from sghi.idr.client.runtime.utils import dispatch

    # Set the application dispatch if not already set. This will allow the
    # runtime to be used as a library easily by requiring only the `setup`
    # funtion to be called. That is, this function should be adequate for
    # initializing the runtime.
    app_dispatcher: dispatch.Dispatcher
    app_dispatcher = app.registry.get(APP_DISPATCHER_REG_KEY)
    if app_dispatcher is None:
        app_dispatcher: dispatch.Dispatcher = dispatch.Dispatcher()
        app.registry.set(APP_DISPATCHER_REG_KEY, app_dispatcher)
    app_dispatcher.send(dispatch.PreConfigSignal())

    settings_dict: dict[str, Any] = dict(DEFAULT_CONFIG)
    settings_dict.update(settings or {})
    initializers: list[SettingInitializer] = list(settings_initializers or [])
    initializers.extend(
        load_settings_initializers(
            settings_dict.get(SETTINGS_INITIALIZERS_CONFIG_KEY, ()),
        ),
    )

    if not disable_default_initializers:
        from .settings_initializers import LoggingInitializer

        initializers.insert(0, LoggingInitializer())
    app.registry.log_level = log_level

    config: Config = Config(
        settings=settings_dict,
        settings_initializers=initializers,
    )
    setattr(app, "settings", config)  # noqa: B010
    app_dispatcher.send(dispatch.PostConfigSignal())
