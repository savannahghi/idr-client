import json
from base64 import b64encode
from typing import Any, Final, Mapping, Optional, Sequence

from app.core import (
    DataSource,
    DataSourceType,
    ExtractMetadata,
    TransportOptions,
)
from app.imp.sql_data import SupportedDBVendors

from .http_api_dialect import HTTPAPIDialect
from .types import HTTPRequestParams

# =============================================================================
# CONSTANTS
# =============================================================================

_AUTH_TRIGGER_STATUS: Final[Sequence[int]] = (401,)

_GET_METHOD: Final[str] = "GET"
_POST_METHOD: Final[str] = "POST"

_REMOTE_SERVER_CONFIG_KEY: Final[str] = "REMOTE_SERVER"


# =============================================================================
# API DIALECT FACTORY
# =============================================================================


def idr_server_api_v1_dialect_factory() -> "IDRServerAPIv1":
    """A factory that returns :class:`IDRServerAPIv1` instances.

    :return: A ``IDRServerAPIv1`` instance.
    """
    import app
    from app.lib import ImproperlyConfiguredError

    remote_server_conf: Optional[Mapping[str, str]] = app.settings.get(
        _REMOTE_SERVER_CONFIG_KEY
    )
    if not remote_server_conf or type(remote_server_conf) is not dict:
        raise ImproperlyConfiguredError(
            message='The "%s" setting is missing, empty or not valid.'
            % _REMOTE_SERVER_CONFIG_KEY
        )
    for _conf_key in ("host", "password", "username"):
        if _conf_key not in remote_server_conf:
            raise ImproperlyConfiguredError(
                message='The setting "%s" MUST be provided as part of the '
                "remote server config." % _conf_key
            )

    return IDRServerAPIv1(
        server_url=remote_server_conf["host"],
        username=remote_server_conf["username"],
        password=remote_server_conf["password"],
    )


# =============================================================================
# API DIALECT
# =============================================================================


class IDRServerAPIv1(HTTPAPIDialect):
    """
    A :class:`HTTPAPIDialect` implementation of the first version of the
    IDR Server API.
    """

    def __init__(self, server_url: str, username: str, password: str):
        from app.lib import ensure_not_none, ensure_not_none_nor_empty

        self._server_url: str = ensure_not_none_nor_empty(
            value=server_url, message='A valid "server_url" MUST be provided.'
        )
        self._username: str = ensure_not_none_nor_empty(
            value=username, message='"username" MUST not be none or empty.'
        )
        self._password: str = ensure_not_none(
            value=password, message='"password" MUST not be none.'
        )
        self._base_url: str = "%s/api" % self._server_url

    # AUTHENTICATION
    # -------------------------------------------------------------------------
    @property
    def auth_trigger_statuses(self) -> Sequence[int]:
        return _AUTH_TRIGGER_STATUS

    def authenticate(self, **options: TransportOptions) -> HTTPRequestParams:
        return {
            "headers": {
                "Accept": "application/json",
                "Authorization": "Basic %s" % self._b64encode_credentials(),
            },
            "expected_http_status_code": 200,
            "method": _POST_METHOD,
            "url": "%s/auth/login/" % self._base_url,
        }

    def response_to_auth(
        self, response_content: bytes, **options: TransportOptions
    ) -> Mapping[str, str]:
        token: str = json.loads(response_content).get("token", "")
        return {"Authorization": "Token %s" % token}

    # DATA SOURCE EXTRACTS RETRIEVAL
    # -------------------------------------------------------------------------
    def fetch_data_source_extracts(
        self,
        data_source_type: DataSourceType,
        data_source: DataSource,
        **options: TransportOptions,
    ) -> HTTPRequestParams:
        return {
            "headers": {"Accept": "application/json"},
            "expected_http_status_code": 200,
            "method": _GET_METHOD,
            "url": "%s/%s/sql_extract_metadata/"
            % (self._base_url, data_source_type.code),
        }

    def response_to_data_source_extracts(
        self,
        response_content: bytes,
        data_source_type: DataSourceType,
        data_source: DataSource,
        **options: TransportOptions,
    ) -> Sequence[ExtractMetadata]:
        # TODO: Add an implementation for .
        from app.lib import Chainable

        dst: DataSourceType = data_source_type
        results: Sequence[Mapping[str, Any]] = json.loads(
            response_content
        ).get("results", tuple())
        return tuple(
            (
                Chainable(_result).
                # Process/clean the response content in preparation for data
                # source initialization.
                execute(
                    lambda _r: {**_r, "applicable_source_version": tuple()}
                ).
                # Initialize the data source.
                execute(
                    lambda _r: (
                        dst.imp_extract_metadata_klass().of_mapping(_r)
                    )
                ).value
                for _result in results
            )
        )

    # DATA SOURCES RETRIEVAL
    # -------------------------------------------------------------------------
    def fetch_data_sources(
        self, data_source_type: DataSourceType, **options: TransportOptions
    ) -> HTTPRequestParams:
        return {
            "headers": {"Accept": "application/json"},
            "expected_http_status_code": 200,
            "method": _GET_METHOD,
            "url": "%s/%s/sql_database_sources/"
            % (self._base_url, data_source_type.code),
        }

    def response_to_data_sources(
        self,
        response_content: bytes,
        data_source_type: DataSourceType,
        **options: TransportOptions,
    ) -> Sequence[DataSource]:
        # TODO: Add support for multiple data source types.
        from app.lib import Chainable

        results: Sequence[Mapping[str, Any]] = json.loads(
            response_content
        ).get("results", tuple())
        return tuple(
            (
                Chainable(_result).
                # Process/clean the response content in preparation for data
                # source initialization.
                execute(
                    lambda _r: {
                        **_r,
                        "database_vendor": SupportedDBVendors.MYSQL,
                    }
                ).
                # Initialize the data source.
                execute(
                    lambda _r: (
                        data_source_type.imp_data_source_klass().of_mapping(_r)
                    )
                ).value
                for _result in results
            )
        )

    # HELPERS
    # -------------------------------------------------------------------------
    def _b64encode_credentials(self) -> str:
        # Copied from requests.auth.BasicAuth
        return b64encode(
            b":".join(
                (
                    self._username.encode("latin1"),
                    self._password.encode("latin1"),
                )
            )
        ).decode("ascii")
