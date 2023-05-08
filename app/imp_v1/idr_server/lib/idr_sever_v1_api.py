from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final

from attrs import define, field
from requests import Request, Response
from requests.auth import AuthBase, HTTPBasicAuth
from requests.models import PreparedRequest

from app.imp_v1.http import (
    HTTPAuthAPIDialect,
    HTTPDataSinkAPIDialect,
    HTTPMetadataSinkAPIDialect,
    HTTPMetadataSourceAPIDialect,
    ResponsePredicate,
    SimpleHTTPDataSinkMetadata,
    if_response_has_status_factory,
)
from app.imp_v1.sql.domain import SimpleSQLDatabaseDescriptor, SimpleSQLQuery

from ..domain import IDRServerV1APIUploadMetadata, ParquetData

# =============================================================================
# CONSTANTS
# =============================================================================

_GET_METHOD: Final[str] = "GET"
_PATH_METHOD: Final[str] = "PATCH"
_POST_METHOD: Final[str] = "POST"

# =============================================================================
# HELPERS
# =============================================================================


def _if_un_authenticated_response(response: Response) -> bool:
    return if_response_has_status_factory(401)(response)


@define(slots=True)
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
    HTTPDataSinkAPIDialect[IDRServerV1APIUploadMetadata, ParquetData],
    HTTPMetadataSinkAPIDialect[IDRServerV1APIUploadMetadata, SimpleSQLQuery],
    HTTPMetadataSourceAPIDialect[
        SimpleHTTPDataSinkMetadata,
        SimpleSQLDatabaseDescriptor,
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
            headers={"Accept": "application/json"},
            method=_POST_METHOD,
            url=f"{self._base_api_url}/auth/login/",
        )

    def handle_auth_response(self, response: Response) -> AuthBase:
        token: str = response.json().get("token")
        return _IDRServerAuth(token)

    # HTTP DATA SINK API DIALECT IMPLEMENTATION
    # -------------------------------------------------------------------------
    def consume_request_factory(
        self,
        upload_meta: IDRServerV1APIUploadMetadata,
        clean_data: ParquetData,
        progress: float,
    ) -> Request:
        return Request(
            data={"chunk_index": -1},
            files={
                "chunk_content": (
                    f"-1_{upload_meta.id}",
                    clean_data.content,
                    upload_meta.content_type,
                ),
            },
            headers={"Accept": "application/json"},
            method=_POST_METHOD,
            url="{api_url}/sql_data/sql_upload_metadata/"
            "{upload_meta_id}/start_chunk_upload/".format(
                api_url=self._base_api_url,
                upload_meta_id=upload_meta.id,
            ),
        )

    def handle_consume_response(
        self,
        response: Response,
        upload_meta: IDRServerV1APIUploadMetadata,
        clean_data: ParquetData,
        progress: float,
    ) -> None:
        raise NotImplementedError

    # HTTP METADATA SINK API DIALECT IMPLEMENTATION
    # -------------------------------------------------------------------------
    def consume_upload_meta_request_factory(
        self,
        upload_meta: IDRServerV1APIUploadMetadata,
    ) -> Request:
        return Request(
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json={
                "chunks": upload_meta.chunks,
                "org_unit_code": upload_meta.org_unit_code,
                "org_unit_name": upload_meta.org_unit_name,
                "content_type": upload_meta.content_type,
                "extract_metadata": upload_meta.extract_metadata.id,
            },
            method=_POST_METHOD,
            url="{api_url}/sql_data/sql_upload_metadata/".format(
                api_url=self._base_api_url,
            ),
        )

    def init_upload_metadata_consumption_request_factory(
        self,
        extract_metadata: SimpleSQLQuery,
        content_type: str,
        **kwargs: Mapping[str, Any],
    ) -> Request:
        raise NotImplementedError

    def handle_consume_upload_meta_response(
        self,
        response: Response,
        upload_meta: IDRServerV1APIUploadMetadata,
    ) -> None:
        raise NotImplementedError

    def handle_init_upload_metadata_consumption_response(
        self,
        response: Response,
        extract_metadata: SimpleSQLQuery,
        content_type: str,
        **kwargs: Mapping[str, Any],
    ) -> IDRServerV1APIUploadMetadata:
        raise NotImplementedError

    # HTTP METADATA SOURCE API DIALECT IMPLEMENTATION
    # -------------------------------------------------------------------------
    def provide_data_sink_meta_request_factory(self) -> Request:
        raise NotImplementedError

    def provide_data_source_meta_request_factory(self) -> Request:
        return Request(
            headers={"Accept": "application/json"},
            method=_GET_METHOD,
            url="{api_url}/sql_data/sql_database_sources/".format(
                api_url=self._base_api_url,
            ),
        )

    def provide_extract_meta_request_factory(
        self,
        data_source: SimpleSQLDatabaseDescriptor,
    ) -> Request:
        raise NotImplementedError

    def handle_provide_data_sink_meta_response(
        self,
        response: Response,
    ) -> Iterable[SimpleHTTPDataSinkMetadata]:
        raise NotImplementedError

    def handle_provide_data_source_meta_response(
        self,
        response: Response,
    ) -> Iterable[SimpleSQLDatabaseDescriptor]:
        results: Sequence[Mapping[str, Any]] = response.json().get(
            "results",
            (),
        )
        return [
            SimpleSQLDatabaseDescriptor(
                id=r["id"],
                name=r["name"],
                description=r["description"],
                database_url="",
                isolation_level="REPEATABLE READ",
            )
            for r in results
        ]

    def handle_provide_extract_meta_response(
        self,
        response: Response,
        data_source: SimpleSQLDatabaseDescriptor,
    ) -> Iterable[SimpleSQLQuery]:
        raise NotImplementedError
