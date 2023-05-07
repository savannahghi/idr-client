from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Any

from attrs import define, field

from app.core_v1 import (
    BaseMetadataSink,
    BaseMetadataSource,
    DataSinkMetadata,
    DataSourceMetadata,
    ExtractMetadata,
    UploadMetadata,
)

from ..lib import (
    HTTPMetadataSinkAPIDialect,
    HTTPMetadataSourceAPIDialect,
    HTTPTransport,
    if_request_accepted,
)
from ..typings import ResponsePredicate

if TYPE_CHECKING:
    from requests.models import Request, Response


@define
class HTTPMetadataSink(BaseMetadataSink):
    """:class:`MetadataSink` backed by an HTTP server."""

    _transport: HTTPTransport = field()
    _api_dialect: HTTPMetadataSinkAPIDialect = field()
    _valid_response_predicate: ResponsePredicate = field(
        default=if_request_accepted,
        kw_only=True,
    )

    @property
    def api_dialect(self) -> HTTPMetadataSinkAPIDialect:
        return self._api_dialect

    def dispose(self) -> None:
        self._is_disposed = True
        self._transport.dispose()

    def consume_upload_meta(self, upload_meta: UploadMetadata) -> None:
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

    def init_upload_metadata_consumption(
        self,
        extract_metadata: ExtractMetadata,
        content_type: str,
        **kwargs: Mapping[str, Any],
    ) -> UploadMetadata:
        req: Request = (
            self._api_dialect.init_upload_metadata_consumption_request_factory(
                extract_metadata=extract_metadata,
                content_type=content_type,
                **kwargs,
            )
        )
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return (
            self._api_dialect.handle_init_upload_metadata_consumption_response(
                response=res,
                extract_metadata=extract_metadata,
                content_type=content_type,
                **kwargs,
            )
        )


class HTTPMetadataSource(BaseMetadataSource):
    """:class:`MetadataSource` backed by an HTTP server."""

    _transport: HTTPTransport = field()
    _api_dialect: HTTPMetadataSourceAPIDialect = field()
    _valid_response_predicate: ResponsePredicate = field(
        default=if_request_accepted,
        kw_only=True,
    )

    @property
    def api_dialect(self) -> HTTPMetadataSourceAPIDialect:
        return self._api_dialect

    def dispose(self) -> None:
        self._is_disposed = True
        self._transport.dispose()

    def provide_data_sink_meta(self) -> Iterable[DataSinkMetadata]:
        req: Request = (
            self._api_dialect.provide_data_sink_meta_request_factory()
        )
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_provide_data_sink_meta_response(res)

    def provide_data_source_meta(self) -> Iterable[DataSourceMetadata]:
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
        data_source: DataSourceMetadata,
    ) -> Iterable[ExtractMetadata]:
        req: Request = self._api_dialect.provide_extract_meta_request_factory(
            data_source=data_source,
        )
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_provide_extract_meta_response(
            response=res,
            data_source=data_source,
        )
