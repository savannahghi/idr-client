from collections.abc import Callable
from typing import TYPE_CHECKING, Generic, Self, TypeVar

from attrs import define, field

from app.core_v1 import (
    BaseDataSink,
    BaseDataSinkStream,
    CleanedData,
    DataSinkMetadata,
    ExtractMetadata,
    RawData,
    UploadMetadata,
)

from ..lib import HTTPDataSinkAPIDialect, HTTPTransport, if_request_accepted
from ..typings import HTTPTransportFactory, ResponsePredicate

if TYPE_CHECKING:
    from requests.models import Request, Response


# =============================================================================
# TYPES
# =============================================================================

_CD = TypeVar("_CD", bound=CleanedData)
_DS = TypeVar("_DS", bound=DataSinkMetadata)
_EM = TypeVar("_EM", bound=ExtractMetadata)
_RD = TypeVar("_RD", bound=RawData)
_T = TypeVar("_T")
_UM = TypeVar("_UM", bound=UploadMetadata)


# =============================================================================
# HTTP OPERATION CLASSES
# =============================================================================


@define(order=False)
class HTTPDataSink(BaseDataSink[_DS, _UM, _CD], Generic[_DS, _UM, _CD]):
    """A :class:`DataSink` backed by an HTTP server."""

    _transport_factory: HTTPTransportFactory = field()
    _api_dialect_factory: Callable[[], HTTPDataSinkAPIDialect[_CD]] = field()
    _valid_response_predicate: ResponsePredicate = field(
        default=if_request_accepted,
        kw_only=True,
    )

    @property
    def api_dialect_factory(
        self,
    ) -> Callable[[], HTTPDataSinkAPIDialect[_CD]]:
        return self._api_dialect_factory

    @property
    def transport_factory(self) -> HTTPTransportFactory:
        return self._transport_factory

    def dispose(self) -> None:
        self._is_disposed = True

    def start_consumption(
        self,
        upload_metadata: _UM,
    ) -> "HTTPDataSinkStream[_UM, _CD]":
        return HTTPDataSinkStream(
            self,
            upload_metadata,
            self._transport_factory(),
            self._api_dialect_factory(),
            valid_response_predicate=self._valid_response_predicate,  # pyright: ignore  # noqa: E501
        )

    @classmethod
    def from_data_sink_meta(cls, data_sink_meta: _DS) -> Self:
        # FIXME: Add a proper implementation for this method
        raise NotImplementedError


@define(order=False)
class HTTPDataSinkStream(BaseDataSinkStream[_UM, _CD], Generic[_UM, _CD]):
    """A :class:`DataSinkStream` backed by an HTTP server."""

    _transport: HTTPTransport = field()
    _api_dialect: HTTPDataSinkAPIDialect[_CD] = field()
    _valid_response_predicate: ResponsePredicate = field(
        default=if_request_accepted,
        kw_only=True,
    )

    @property
    def api_dialect(self) -> HTTPDataSinkAPIDialect[_CD]:
        return self._api_dialect

    @property
    def transport(self) -> HTTPTransport:
        return self._transport

    def consume(
        self,
        clean_data: _CD,
        progress: float,
    ) -> None:
        req: Request = self._api_dialect.consume_request_factory(
            clean_data=clean_data,
            progress=progress,
        )
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_consume_response(
            response=res,
            clean_data=clean_data,
            progress=progress,
        )

    def dispose(self) -> None:
        self._is_disposed = True
        self._transport.dispose()
