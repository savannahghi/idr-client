from __future__ import annotations

from collections.abc import Iterable, Mapping
from functools import cache
from typing import TYPE_CHECKING, Any, Final, Literal, TypedDict, cast

import sghi.idr.client.core as app
from attrs import define, field, frozen
from requests import Request, Response
from requests.auth import AuthBase, HTTPBasicAuth
from sghi.idr.client import core
from sghi.idr.client.core.lib.config import ImproperlyConfiguredError
from sghi.idr.client.http import (
    HTTPAuthAPIDialect,
    HTTPDataSinkAPIDialect,
    HTTPDrainMetadataFactoryAPIDialect,
    HTTPMetadataConsumerAPIDialect,
    HTTPMetadataSupplierAPIDialect,
    ResponsePredicate,
    SimpleHTTPDataSinkMetadata,
    if_response_has_status_factory,
)
from sghi.idr.client.http.lib.http_transport import HTTPTransport
from sghi.idr.client.sql.domain import (
    PDDataFrameDataSourceStream,
    SimpleSQLDatabaseDescriptor,
    SimpleSQLQuery,
)
from toolz import pipe
from toolz.curried import map

from ..domain import IDRServerV1APIDrainMetadata, ParquetData

if TYPE_CHECKING:
    from requests.models import PreparedRequest
    from sqlalchemy.engine.url import URL


# =============================================================================
# TYPES
# =============================================================================


class _IDRServerDataSourceAPIPayload(TypedDict):
    id: str  # noqa: A003
    name: str
    description: str | None
    database_name: str
    database_vendor: Literal["mysql", "postgres"]


class _IDRServerExtractMetaAPIPayload(TypedDict):
    id: str  # noqa: A003
    name: str
    description: str | None
    data_source: _IDRServerDataSourceAPIPayload
    sql_query: str
    version: str


class _IDRServerUploadMetaAPIPayload(TypedDict):
    id: str  # noqa: A003
    chunks_count: int
    start_time: str
    finish_time: str | None
    org_unit_code: str
    org_unit_name: str
    content_type: str
    extract_metadata: str


# =============================================================================
# CONSTANTS
# =============================================================================

_GET_METHOD: Final[str] = "GET"
_PATCH_METHOD: Final[str] = "PATCH"
_POST_METHOD: Final[str] = "POST"

# =============================================================================
# HELPERS
# =============================================================================


def _get_db_instance_url(db_instance_name: str) -> URL:
    if db_instance_name not in app.settings.DATABASE_INSTANCES:
        _err_msg: str = 'No such db instance "{}" configured.'.format(
            db_instance_name,
        )
        raise ImproperlyConfiguredError(message=_err_msg)
    return app.settings.DATABASE_INSTANCES.get(db_instance_name).db_url


def _if_un_authenticated_response(response: Response) -> bool:
    return if_response_has_status_factory(401)(response)


def http_transport_factory() -> HTTPTransport:
    http_transport_settings: Mapping[str, int | float]
    http_transport_settings = core.settings.get("HTTP_TRANSPORT", {})
    return HTTPTransport(
        auth_api_dialect=idr_server_api_factory(),  # pyright: ignore
        connect_timeout=http_transport_settings.get(  # pyright: ignore
            "connect_timeout",
            60,
        ),
        read_timeout=http_transport_settings.get(  # pyright: ignore
            "read_timeout",
            60,
        ),
    )


@cache
def idr_server_api_factory() -> IDRServerV1API:
    idr_server_settings: Mapping[str, str] = core.settings.IDR_SERVER_SETTINGS
    return IDRServerV1API(
        server_url=idr_server_settings["host"],  # pyright: ignore
        username=idr_server_settings["username"],  # pyright: ignore
        password=idr_server_settings["password"],  # pyright: ignore
    )


@frozen
class _IDRServerAuth(AuthBase):
    """
    The :class:`~requests.auth.AuthBase` implementation used by the IDR Server.
    """

    _token: str = field()

    def __call__(
        self,
        r: PreparedRequest,
        *args: Any,  # noqa: ANN401
        **kwargs: Any,  # noqa: ANN401
    ) -> PreparedRequest:
        r.headers.update({"Authorization": f"Token {self._token}"})
        return r


# =============================================================================
# IDR SERVER V1 API
# =============================================================================


@define(slots=True)
class IDRServerV1API(
    HTTPAuthAPIDialect,
    HTTPDataSinkAPIDialect[IDRServerV1APIDrainMetadata, ParquetData],
    HTTPMetadataConsumerAPIDialect[IDRServerV1APIDrainMetadata],
    HTTPMetadataSupplierAPIDialect[
        SimpleHTTPDataSinkMetadata,
        SimpleSQLDatabaseDescriptor,
        SimpleSQLQuery,
    ],
    HTTPDrainMetadataFactoryAPIDialect[
        IDRServerV1APIDrainMetadata,
        SimpleSQLQuery,
    ],
):
    _server_url: str = field()
    _username: str = field()
    _password: str = field()

    def __attrs_post_init__(self):
        self._base_api_url: str = "{server_url}/api".format(
            server_url=self._server_url,
        )
        self._common_headers: Mapping[str, str] = {
            "Accept": "application/json",
        }

    # HTTP AUTH API DIALECT IMPLEMENTATION
    # -------------------------------------------------------------------------
    @property
    def re_authenticate_predicate(self) -> ResponsePredicate:
        return _if_un_authenticated_response

    def auth_request_factory(self) -> Request:
        return Request(
            auth=HTTPBasicAuth(
                username=self._username,
                password=self._password,
            ),
            headers=self._common_headers,
            method=_POST_METHOD,
            url=f"{self._base_api_url}/auth/login/",
        )

    def handle_auth_response(self, response: Response) -> AuthBase:
        token: str = response.json().get("token")
        return _IDRServerAuth(token)

    # HTTP DATA SINK API DIALECT IMPLEMENTATION
    # -------------------------------------------------------------------------
    def drain_request_factory(
        self,
        drain_meta: IDRServerV1APIDrainMetadata,
        clean_data: ParquetData,
        progress: float,
    ) -> Request:
        return Request(
            data={"chunk_index": clean_data.index},
            files={
                "chunk_content": (
                    f"{clean_data.index}_{drain_meta.id}",
                    clean_data.content.getvalue(),
                    clean_data.content_type,
                ),
            },
            headers=self._common_headers,
            method=_POST_METHOD,
            url="{api_url}/sql_data/sql_upload_metadata/"
            "{upload_meta_id}/start_chunk_upload/".format(
                api_url=self._base_api_url,
                upload_meta_id=drain_meta.id,
            ),
        )

    def handle_drain_response(
        self,
        response: Response,
        drain_meta: IDRServerV1APIDrainMetadata,
        clean_data: ParquetData,
        progress: float,
    ) -> None:
        response.close()
        return

    # HTTP METADATA SINK API DIALECT IMPLEMENTATION
    # -------------------------------------------------------------------------
    def take_drain_meta_request_factory(
        self,
        drain_meta: IDRServerV1APIDrainMetadata,
    ) -> Request:
        return Request(
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json={
                "chunks": drain_meta.chunks,
                "org_unit_code": drain_meta.org_unit_code,
                "org_unit_name": drain_meta.org_unit_name,
                # This is hard-coded content type is bad, but it is required by
                # this version of the IDR Server API.
                "content_type": "application/vnd.apache-parquet",
                "extract_metadata": drain_meta.draw_metadata.id,
            },
            method=_PATCH_METHOD,
            url="{api_url}/sql_data/sql_upload_metadata/"
            "{upload_meta_id}/mark_as_complete/".format(
                api_url=self._base_api_url,
                upload_meta_id=drain_meta.id,
            ),
        )

    def handle_take_drain_meta_response(
        self,
        response: Response,
        drain_meta: IDRServerV1APIDrainMetadata,
    ) -> None:
        response.close()
        return

    # HTTP METADATA SOURCE API DIALECT IMPLEMENTATION
    # -------------------------------------------------------------------------
    def get_data_sink_meta_request_factory(self) -> Request:
        return Request(
            headers=self._common_headers,
            method=_GET_METHOD,
            # This is a dummy call since IDR Server does not offer this API.
            url=f"{self._base_api_url}/",
        )

    def get_data_source_meta_request_factory(self) -> Request:
        return Request(
            headers=self._common_headers,
            method=_GET_METHOD,
            url="{api_url}/sql_data/sql_database_sources/".format(
                api_url=self._base_api_url,
            ),
        )

    def get_draw_meta_request_factory(
        self,
        data_source_meta: SimpleSQLDatabaseDescriptor,
    ) -> Request:
        return Request(
            headers=self._common_headers,
            method=_GET_METHOD,
            params={"data_source": data_source_meta.id},
            url="{api_url}/sql_data/sql_extract_metadata/".format(
                api_url=self._base_api_url,
            ),
        )

    def handle_get_data_sink_meta_response(
        self,
        response: Response,
    ) -> Iterable[SimpleHTTPDataSinkMetadata]:
        response.close()
        return (
            SimpleHTTPDataSinkMetadata(
                id="fyj-cbs-http-data-sink",  # pyright: ignore
                name="FyJ CBS HTTP Data Sink",  # pyright: ignore
                api_dialect_factory=idr_server_api_factory,  # pyright: ignore
                transport_factory=http_transport_factory,  # pyright: ignore
            ),
        )

    def handle_get_data_source_meta_response(
        self,
        response: Response,
    ) -> Iterable[SimpleSQLDatabaseDescriptor]:
        _result: _IDRServerDataSourceAPIPayload
        return cast(
            Iterable[SimpleSQLDatabaseDescriptor],
            pipe(
                response.json().get("results", ()),
                map(
                    lambda _result: {
                        "id": _result["id"],
                        "name": _result["name"],
                        "description": _result.get("description"),
                        "database_url": _get_db_instance_url(
                            _result["database_name"],
                        ),
                        "isolation_level": "REPEATABLE READ",
                        "data_source_stream_factory": PDDataFrameDataSourceStream.of,  # noqa: E501
                    },
                ),
                map(lambda _kwargs: SimpleSQLDatabaseDescriptor(**_kwargs)),
                tuple,
            ),
        )

    def handle_get_draw_meta_response(
        self,
        response: Response,
        data_source_meta: SimpleSQLDatabaseDescriptor,
    ) -> Iterable[SimpleSQLQuery]:
        _result: _IDRServerExtractMetaAPIPayload
        return cast(
            Iterable[SimpleSQLQuery],
            pipe(
                response.json().get("results", ()),
                map(
                    lambda _result: {
                        "id": _result["id"],
                        "name": _result["name"],
                        "description": _result.get("description"),
                        "data_source_metadata": data_source_meta,
                        "raw_sql_query": _result["sql_query"],
                    },
                ),
                map(lambda _kwargs: SimpleSQLQuery(**_kwargs)),
                tuple,
            ),
        )

    # HTTP UPLOAD METADATA API DIALECT IMPLEMENTATION
    # -------------------------------------------------------------------------
    def new_drain_meta_request_factory(
        self,
        draw_meta: SimpleSQLQuery,
    ) -> Request:
        org_unit_code: str = app.settings.LOCATION_ID
        org_unit_name: str = app.settings.LOCATION_NAME
        return Request(
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json={
                "chunks": 0,
                "org_unit_code": org_unit_code,
                "org_unit_name": org_unit_name,
                # This is hard-coded content type is bad, but it is required by
                # this version of the IDR Server API.
                "content_type": "application/vnd.apache-parquet",
                "extract_metadata": draw_meta.id,
            },
            method=_POST_METHOD,
            url="{api_url}/sql_data/sql_upload_metadata/".format(
                api_url=self._base_api_url,
            ),
        )

    def handle_new_drain_meta_response(
        self,
        response: Response,
        draw_meta: SimpleSQLQuery,
    ) -> IDRServerV1APIDrainMetadata:
        result: _IDRServerUploadMetaAPIPayload = response.json()
        return IDRServerV1APIDrainMetadata(
            id=result["id"],  # pyright: ignore
            draw_metadata=draw_meta,  # pyright: ignore
            chunks=result["chunks_count"],  # pyright: ignore
            org_unit_code=result["org_unit_code"],  # pyright: ignore
            org_unit_name=result["org_unit_name"],  # pyright: ignore
        )
