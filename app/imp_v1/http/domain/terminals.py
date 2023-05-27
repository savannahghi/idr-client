from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from attrs import define, field

from app.core_v1 import (
    BaseMetadataSink,
    BaseMetadataSource,
    BaseUploadMetadataFactory,
    DataSinkMetadata,
    DataSourceMetadata,
    ExtractMetadata,
    UploadMetadata,
)

from ..lib import (
    HTTPMetadataSinkAPIDialect,
    HTTPMetadataSourceAPIDialect,
    HTTPTransport,
    HTTPUploadMetadataFactoryAPIDialect,
    if_request_accepted,
)
from ..typings import ResponsePredicate

if TYPE_CHECKING:
    from requests.models import Request, Response

# =============================================================================
# TYPES
# =============================================================================

_DM = TypeVar("_DM", bound=DataSourceMetadata)
_DS = TypeVar("_DS", bound=DataSinkMetadata)
_EM = TypeVar("_EM", bound=ExtractMetadata)
_UM = TypeVar("_UM", bound=UploadMetadata)


# =============================================================================
# HTTP SKELETAL IMPLEMENTATIONS
# =============================================================================


@define(slots=True, order=False)
class HTTPMetadataSink(BaseMetadataSink[_UM], Generic[_UM]):
    """:class:`MetadataSink` backed by an HTTP server."""

    _transport: HTTPTransport = field()
    _api_dialect: HTTPMetadataSinkAPIDialect[_UM] = field()
    _valid_response_predicate: ResponsePredicate = field(
        default=if_request_accepted,
        kw_only=True,
    )

    @property
    def api_dialect(self) -> HTTPMetadataSinkAPIDialect[_UM]:
        return self._api_dialect

    def dispose(self) -> None:
        self._is_disposed = True
        self._transport.dispose()

    def consume_upload_meta(self, upload_meta: _UM) -> None:
        req: Request = self._api_dialect.consume_upload_meta_request_factory(
            upload_meta=upload_meta,
        )
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_consume_upload_meta_response(
            response=res,
            upload_meta=upload_meta,
        )


@define(slots=True, order=False)
class HTTPMetadataSource(
    BaseMetadataSource[_DS, _DM, _EM],
    Generic[_DS, _DM, _EM],
):
    """:class:`MetadataSource` backed by an HTTP server."""

    _transport: HTTPTransport = field()
    _api_dialect: HTTPMetadataSourceAPIDialect[_DS, _DM, _EM] = field()
    _valid_response_predicate: ResponsePredicate = field(
        default=if_request_accepted,
        kw_only=True,
    )

    @property
    def api_dialect(self) -> HTTPMetadataSourceAPIDialect[_DS, _DM, _EM]:
        return self._api_dialect

    def dispose(self) -> None:
        self._is_disposed = True
        self._transport.dispose()

    def provide_data_sink_meta(self) -> Iterable[_DS]:
        req: Request = (
            self._api_dialect.provide_data_sink_meta_request_factory()
        )
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_provide_data_sink_meta_response(res)

    def provide_data_source_meta(self) -> Iterable[_DM]:
        req: Request = (
            self._api_dialect.provide_data_source_meta_request_factory()
        )
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_provide_data_source_meta_response(res)

    def provide_extract_meta(
        self,
        data_source_meta: _DM,
    ) -> Iterable[_EM]:
        req: Request = self._api_dialect.provide_extract_meta_request_factory(
            data_source_meta=data_source_meta,
        )
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_provide_extract_meta_response(
            response=res,
            data_source_meta=data_source_meta,
        )


@define(slots=True, order=False)
class HTTPUploadMetadataFactory(
    BaseUploadMetadataFactory[_UM, _EM],
    Generic[_UM, _EM],
):
    """:class:`UploadMetadataFactory` backed by an HTTP server."""

    _transport: HTTPTransport = field()
    _api_dialect: HTTPUploadMetadataFactoryAPIDialect[_UM, _EM] = field()
    _valid_response_predicate: ResponsePredicate = field(
        default=if_request_accepted,
        kw_only=True,
    )

    @property
    def api_dialect(self) -> HTTPUploadMetadataFactoryAPIDialect[_UM, _EM]:
        return self._api_dialect

    def dispose(self) -> None:
        self._transport.dispose()
        self._is_disposed = True

    def new_upload_meta(
        self,
        extract_meta: _EM,
        content_type: str,
        **kwargs: Mapping[str, Any],
    ) -> _UM:
        req: Request = self._api_dialect.new_upload_meta_request_factory(
            extract_meta=extract_meta,
            content_type=content_type,
            **kwargs,
        )
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_new_upload_meta_response(
            response=res,
            extract_meta=extract_meta,
            content_type=content_type,
            **kwargs,
        )
