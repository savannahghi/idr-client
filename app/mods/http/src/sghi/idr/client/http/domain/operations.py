import logging
from collections.abc import Callable
from logging import Logger
from typing import TYPE_CHECKING, Generic, Self, TypeVar

from attrs import define, field
from sghi.idr.client.core.domain import (
    BaseDataSink,
    BaseDataSinkStream,
    CleanedData,
    DrainMetadata,
    DrawMetadata,
    RawData,
)
from sghi.idr.client.core.lib import type_fqn

from ..lib import HTTPDataSinkAPIDialect, HTTPTransport, if_request_accepted
from ..typings import HTTPTransportFactory, ResponsePredicate
from .metadata import BaseHTTPDataSinkMetadata

if TYPE_CHECKING:
    from requests.models import Request, Response


# =============================================================================
# TYPES
# =============================================================================

_CD = TypeVar("_CD", bound=CleanedData)
_DS = TypeVar("_DS", bound=BaseHTTPDataSinkMetadata)
_EM = TypeVar("_EM", bound=DrawMetadata)
_RD = TypeVar("_RD", bound=RawData)
_T = TypeVar("_T")
_UM = TypeVar("_UM", bound=DrainMetadata)


# =============================================================================
# HTTP OPERATION CLASSES
# =============================================================================


@define(order=False)
class HTTPDataSink(BaseDataSink[_DS, _UM, _CD], Generic[_DS, _UM, _CD]):
    """A :class:`DataSink` backed by an HTTP server."""

    _transport_factory: HTTPTransportFactory = field()
    _api_dialect_factory: Callable[
        [],
        HTTPDataSinkAPIDialect[_UM, _CD],
    ] = field()
    _valid_response_predicate: ResponsePredicate = field(
        default=if_request_accepted,
        kw_only=True,
    )

    def __attrs_post_init__(self) -> None:
        self._logger: Logger = logging.getLogger(type_fqn(self.__class__))

    @property
    def api_dialect_factory(
        self,
    ) -> Callable[[], HTTPDataSinkAPIDialect[_UM, _CD]]:
        return self._api_dialect_factory

    @property
    def transport_factory(self) -> HTTPTransportFactory:
        return self._transport_factory

    def dispose(self) -> None:
        self._is_disposed = True
        self._logger.debug("Disposal complete.")

    def start_drain(
        self,
        drain_metadata: _UM,
    ) -> "HTTPDataSinkStream[_UM, _CD]":
        self._logger.info('Start drain for metadata "%s".', drain_metadata)
        return HTTPDataSinkStream(
            self,
            drain_metadata,
            self._transport_factory(),
            self._api_dialect_factory(),
            valid_response_predicate=self._valid_response_predicate,  # pyright: ignore  # noqa: E501
        )

    @classmethod
    def of_data_sink_meta(cls, data_sink_meta: _DS) -> Self:
        return cls(
            name=data_sink_meta.name,  # pyright: ignore
            description=data_sink_meta.description,  # pyright: ignore
            data_sink_meta=data_sink_meta,  # pyright: ignore
            transport_factory=data_sink_meta.transport_factory,  # pyright: ignore  # noqa: E501
            api_dialect_factory=data_sink_meta.api_dialect_factory,  # pyright: ignore  # noqa: E501
            valid_response_predicate=data_sink_meta.valid_response_predicate,  # pyright: ignore  # noqa: E501
        )


@define(order=False)
class HTTPDataSinkStream(BaseDataSinkStream[_UM, _CD], Generic[_UM, _CD]):
    """A :class:`DataSinkStream` backed by an HTTP server."""

    _transport: HTTPTransport = field()
    _api_dialect: HTTPDataSinkAPIDialect[_UM, _CD] = field()
    _valid_response_predicate: ResponsePredicate = field(
        default=if_request_accepted,
        kw_only=True,
    )

    def __attrs_post_init__(self) -> None:
        self._logger: Logger = logging.getLogger(type_fqn(self.__class__))

    @property
    def api_dialect(self) -> HTTPDataSinkAPIDialect[_UM, _CD]:
        return self._api_dialect

    @property
    def transport(self) -> HTTPTransport:
        return self._transport

    def drain(self, clean_data: _CD, progress: float) -> None:
        self._logger.info("Drain cleaned data, progress = %d.", progress)
        req: Request = self._api_dialect.drain_request_factory(
            drain_meta=self.drain_metadata,
            clean_data=clean_data,
            progress=progress,
        )
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_drain_response(
            response=res,
            drain_meta=self.drain_metadata,
            clean_data=clean_data,
            progress=progress,
        )

    def dispose(self) -> None:
        self._is_disposed = True
        self._transport.dispose()
        self._logger.debug("Disposal complete.")
