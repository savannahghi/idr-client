import json
from base64 import b64encode
from collections.abc import Mapping, Sequence
from typing import Any, Final

from app.core import (
    DataSource,
    DataSourceType,
    ExtractMetadata,
    TransportOptions,
    UploadChunk,
    UploadMetadata,
)
from app.imp.sql_data import SupportedDBVendors

from .http_api_dialect import HTTPAPIDialect
from .types import HTTPRequestParams

# =============================================================================
# CONSTANTS
# =============================================================================

_AUTH_TRIGGER_STATUS: Final[Sequence[int]] = (401,)

_GET_METHOD: Final[str] = "GET"
_PATCH_METHOD: Final[str] = "PATCH"
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

    remote_server_conf: Mapping[str, str] | None = app.settings.get(
        _REMOTE_SERVER_CONFIG_KEY,
    )
    if not remote_server_conf or type(remote_server_conf) is not dict:
        err_msg: str = (
            'The "%s" setting is missing, empty or not valid.'
            % _REMOTE_SERVER_CONFIG_KEY
        )
        raise ImproperlyConfiguredError(message=err_msg)
    for _conf_key in ("host", "password", "username"):
        if _conf_key not in remote_server_conf:
            err_msg: str = (
                'The setting "%s" MUST be provided as part of the remote '
                "server config." % _conf_key
            )
            raise ImproperlyConfiguredError(message=err_msg)

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
            value=server_url,
            message='A valid "server_url" MUST be provided.',
        )
        self._username: str = ensure_not_none_nor_empty(
            value=username,
            message='"username" MUST not be none or empty.',
        )
        self._password: str = ensure_not_none(
            value=password,
            message='"password" MUST not be none.',
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
        self,
        response_content: bytes,
        **options: TransportOptions,
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
            "params": {"data_source": data_source.id},
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
            response_content,
        ).get("results", ())
        return tuple(
            Chainable(_result).
            # Process/clean the response content in preparation for data
            # source initialization.
            execute(
                lambda _r: {
                    **_r,
                    "applicable_source_version": (),
                    "data_source": data_source,
                },
            ).
            # Initialize the data source.
            execute(
                lambda _r: (dst.imp_extract_metadata_klass().of_mapping(_r)),
            ).value
            for _result in results
        )

    # DATA SOURCES RETRIEVAL
    # -------------------------------------------------------------------------
    def fetch_data_sources(
        self,
        data_source_type: DataSourceType,
        **options: TransportOptions,
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
            response_content,
        ).get("results", ())
        return tuple(
            Chainable(_result).
            # Process/clean the response content in preparation for data
            # source initialization.
            execute(
                lambda _r: {
                    **_r,
                    "database_vendor": SupportedDBVendors.MYSQL,
                    "data_source_type": data_source_type,
                },
            ).
            # Initialize the data source.
            execute(
                lambda _r: (
                    data_source_type.imp_data_source_klass().of_mapping(_r)
                ),
            ).value
            for _result in results
        )

    # MARK UPLOAD COMPLETION
    # -------------------------------------------------------------------------
    def mark_upload_as_complete(
        self,
        upload_metadata: UploadMetadata,
        **options: TransportOptions,
    ) -> HTTPRequestParams:
        parent_ds: DataSource = upload_metadata.extract_metadata.data_source
        parent_dst: DataSourceType = parent_ds.data_source_type
        return {
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            "expected_http_status_code": 200,
            "method": _PATCH_METHOD,
            "url": "%s/%s/sql_upload_metadata/%s/mark_as_complete/"
            % (self._base_url, parent_dst.code, upload_metadata.id),
            "data": json.dumps({}),
        }

    # UPLOAD CHUNK POSTAGE
    # -------------------------------------------------------------------------
    def post_upload_chunk(
        self,
        upload_metadata: UploadMetadata,
        chunk_index: int,
        chunk_content: bytes,
        extra_init_kwargs: Mapping[str, Any] | None = None,
        **options: TransportOptions,
    ) -> HTTPRequestParams:
        parent_ds: DataSource = upload_metadata.extract_metadata.data_source
        parent_dst: DataSourceType = parent_ds.data_source_type
        return {
            "headers": {
                "Accept": "application/json",
                # "Content-Type": "multipart/form-data",
            },
            "expected_http_status_code": 201,
            "method": _POST_METHOD,
            "url": "%s/%s/sql_upload_metadata/%s/start_chunk_upload/"
            % (self._base_url, parent_dst.code, upload_metadata.id),
            "data": {"chunk_index": chunk_index},
            "files": {
                "chunk_content": (
                    "%d_%s" % (chunk_index, upload_metadata.id),
                    chunk_content,
                    upload_metadata.content_type,
                ),
            },
        }

    def response_to_upload_chunk(
        self,
        response_content: bytes,
        upload_metadata: UploadMetadata,
        **options: TransportOptions,
    ) -> UploadChunk:
        result: Mapping[str, Any] = json.loads(response_content)

        parent_ds: DataSource = upload_metadata.extract_metadata.data_source
        parent_dst: DataSourceType = parent_ds.data_source_type
        return parent_dst.imp_upload_chunk_klass().of_mapping(result)

    # UPLOAD METADATA POSTAGE
    # -------------------------------------------------------------------------
    def post_upload_metadata(
        self,
        extract_metadata: ExtractMetadata,
        content_type: str,
        org_unit_code: str,
        org_unit_name: str,
        extra_init_kwargs: Mapping[str, Any] | None = None,
        **options: TransportOptions,
    ) -> HTTPRequestParams:
        parent_ds: DataSource = extract_metadata.data_source
        parent_dst: DataSourceType = parent_ds.data_source_type
        return {
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            "expected_http_status_code": 201,
            "method": _POST_METHOD,
            "url": "%s/%s/sql_upload_metadata/"
            % (self._base_url, parent_dst.code),
            "data": json.dumps(
                {
                    "chunks": 1,
                    "org_unit_code": org_unit_code,
                    "org_unit_name": org_unit_name,
                    "content_type": content_type,
                    "extract_metadata": extract_metadata.id,
                },
            ),
        }

    def response_to_upload_metadata(
        self,
        response_content: bytes,
        extract_metadata: ExtractMetadata,
        **options: TransportOptions,
    ) -> UploadMetadata:
        from app.lib import Chainable

        result: Mapping[str, Any] = json.loads(response_content)
        parent_ds: DataSource = extract_metadata.data_source
        parent_dst: DataSourceType = parent_ds.data_source_type

        # Process/clean the response content in preparation for data
        # source initialization.
        return (
            Chainable(value=result)
            .execute(lambda _r: {**_r, "extract_metadata": extract_metadata})
            .execute(
                lambda _r: parent_dst.imp_upload_metadata_klass().of_mapping(
                    _r,
                ),
            )
            .value
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
                ),
            ),
        ).decode("ascii")
