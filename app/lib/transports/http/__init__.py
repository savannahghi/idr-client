from collections.abc import Callable, Mapping
from typing import Any, Final, cast

from .api_v1_dialect import IDRServerAPIv1, idr_server_api_v1_dialect_factory
from .http_api_dialect import HTTPAPIDialect
from .http_transport import HTTPTransport

# =============================================================================
# TYPES
# =============================================================================

_HTTPAPIDialectFactory = Callable[[], HTTPAPIDialect]


# =============================================================================
# CONSTANTS
# =============================================================================

_DEFAULT_API_DIALECT_FACTORY_CONF_KEY: Final[
    str
] = "default_http_api_dialect_factory"

_HTTP_TRANSPORT_CONFIG_KEY: Final[str] = "HTTP_TRANSPORT"


# =============================================================================
# FACTORIES
# =============================================================================


def http_transport_factory() -> HTTPTransport:
    """A factory that returns :class:`HTTPTransport` instances.

    :return: a ``HTTPTransport`` instance.
    """
    import app
    from app.lib import ImproperlyConfiguredError, import_string

    http_transport_conf: Mapping[str, Any] | None = app.settings.get(
        _HTTP_TRANSPORT_CONFIG_KEY,
    )
    if not (http_transport_conf and isinstance(http_transport_conf, dict)):
        err_msg: str = (
            'The "%s" setting is missing, empty or not valid.'
            % _HTTP_TRANSPORT_CONFIG_KEY
        )
        raise ImproperlyConfiguredError(message=err_msg)

    api_dialect_factory_path: str | None = http_transport_conf.get(
        _DEFAULT_API_DIALECT_FACTORY_CONF_KEY,
    )
    if not api_dialect_factory_path:
        err_msg: str = (
            'The setting "%s" MUST be provided as part of the http transport '
            "config." % _DEFAULT_API_DIALECT_FACTORY_CONF_KEY
        )
        raise ImproperlyConfiguredError(message=err_msg)

    api_dialect_factory: _HTTPAPIDialectFactory
    try:
        api_dialect_factory = cast(
            _HTTPAPIDialectFactory,
            import_string(api_dialect_factory_path),
        )
    except (ImportError, TypeError) as exp:
        err_msg: str = (
            'Unable to import the http api dialect factory at "%s". Ensure a '
            "valid path was given." % api_dialect_factory_path
        )
        raise ImproperlyConfiguredError(message=err_msg) from exp

    return HTTPTransport(
        api_dialect=api_dialect_factory(),
        connect_timeout=http_transport_conf.get("connect_timeout"),
        read_timeout=http_transport_conf.get("read_timeout"),
    )


__all__ = [
    "HTTPAPIDialect",
    "HTTPTransport",
    "IDRServerAPIv1",
    "http_transport_factory",
    "idr_server_api_v1_dialect_factory",
]
