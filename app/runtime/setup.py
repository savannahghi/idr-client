from collections.abc import Mapping, Sequence
from typing import Any, cast

from toolz import first, pipe
from toolz.curried import groupby, map, valmap

import app
from app.core.domain import ETLProtocol
from app.lib import (
    Config,
    ImproperlyConfiguredError,
    SettingInitializer,
    import_string_as_klass,
)

from .constants import (
    DEFAULT_CONFIG,
    ETL_PROTOCOLS_CONFIG_KEY,
    SETTINGS_INITIALIZERS_CONFIG_KEY,
)
from .typings import ETLProtocol_Factory

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
        return initializer_klass()  # type: ignore
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


def _etl_protocol_factory_to_instance(
    _etl_protocol_factory: ETLProtocol_Factory,
) -> ETLProtocol:
    _etl_protocol_instance: ETLProtocol = _etl_protocol_factory()
    if not isinstance(_etl_protocol_instance, ETLProtocol):
        _err_msg: str = (
            'Invalid ETLProtocol, the factory "{}.{}" returned an instance '
            'that is not a subclass of "app.core.domain.ETLProtocol".'.format(
                # noinspection PyUnresolvedReferences
                _etl_protocol_factory.__module__,
                _etl_protocol_factory.__qualname__,
            )
        )
        raise ImproperlyConfiguredError(message=_err_msg)

    return _etl_protocol_instance


def _initialize_and_load_etl_protocols(
    etl_protocol_factories: Sequence[ETLProtocol_Factory],
) -> None:
    app.registry.etl_protocols = cast(
        Mapping[str, ETLProtocol],
        pipe(
            etl_protocol_factories,
            map(_etl_protocol_factory_to_instance),
            groupby(lambda _ep: _ep.id),
            valmap(first),
        ),
    )


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
    settings_dict: dict[str, Any] = dict(DEFAULT_CONFIG)
    settings_dict.update(settings or {})
    initializers: list[SettingInitializer] = list(settings_initializers or [])
    initializers.extend(
        load_settings_initializers(
            settings_dict.get(SETTINGS_INITIALIZERS_CONFIG_KEY, ()),
        ),
    )

    if not disable_default_initializers:
        from .settings_initializers import (
            ETLProtocolInitializer,
            LoggingInitializer,
        )

        initializers.insert(0, LoggingInitializer())
        initializers.insert(1, ETLProtocolInitializer())
    app.registry.log_level = log_level
    # noinspection
    app.settings = Config(
        settings=settings_dict,
        settings_initializers=initializers,
    )
    _initialize_and_load_etl_protocols(
        app.settings.get(ETL_PROTOCOLS_CONFIG_KEY, []),
    )
