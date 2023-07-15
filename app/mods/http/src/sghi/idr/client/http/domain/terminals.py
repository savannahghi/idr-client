import logging
from collections.abc import Iterable
from logging import Logger
from typing import TYPE_CHECKING, Generic, TypeVar

from attrs import define, field
from sghi.idr.client.core.domain import (
    BaseDrainMetadataFactory,
    BaseMetadataConsumer,
    BaseMetadataSupplier,
    DataSinkMetadata,
    DataSourceMetadata,
    DrainMetadata,
    DrawMetadata,
)
from sghi.idr.client.core.lib import type_fqn

from ..lib import (
    HTTPDrainMetadataFactoryAPIDialect,
    HTTPMetadataConsumerAPIDialect,
    HTTPMetadataSupplierAPIDialect,
    HTTPTransport,
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
_EM = TypeVar("_EM", bound=DrawMetadata)
_UM = TypeVar("_UM", bound=DrainMetadata)


# =============================================================================
# HTTP SKELETAL IMPLEMENTATIONS
# =============================================================================


@define(slots=True, order=False)
class HTTPDrainMetadataFactory(
    BaseDrainMetadataFactory[_UM, _EM],
    Generic[_UM, _EM],
):
    """:class:`DrainMetadataFactory` backed by an HTTP server."""

    _transport: HTTPTransport = field()
    _api_dialect: HTTPDrainMetadataFactoryAPIDialect[_UM, _EM] = field()
    _valid_response_predicate: ResponsePredicate = field(
        default=if_request_accepted,
        kw_only=True,
    )

    def __attrs_post_init__(self) -> None:
        self._logger: Logger = logging.getLogger(type_fqn(self.__class__))

    @property
    def api_dialect(self) -> HTTPDrainMetadataFactoryAPIDialect[_UM, _EM]:
        return self._api_dialect

    def dispose(self) -> None:
        self._is_disposed = True
        self._transport.dispose()
        self._logger.debug("Disposal complete.")

    def new_drain_meta(self, draw_meta: _EM) -> _UM:
        self._logger.info(
            'Create new drain metadata using draw metadata "%s".',
            draw_meta,
        )
        req: Request = self._api_dialect.new_drain_meta_request_factory(
            draw_meta=draw_meta,
        )
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_new_drain_meta_response(
            response=res,
            draw_meta=draw_meta,
        )


@define(slots=True, order=False)
class HTTPMetadataConsumer(BaseMetadataConsumer[_UM], Generic[_UM]):
    """:class:`MetadataConsumer` backed by an HTTP server."""

    _transport: HTTPTransport = field()
    _api_dialect: HTTPMetadataConsumerAPIDialect[_UM] = field()
    _valid_response_predicate: ResponsePredicate = field(
        default=if_request_accepted,
        kw_only=True,
    )

    def __attrs_post_init__(self) -> None:
        self._logger: Logger = logging.getLogger(type_fqn(self.__class__))

    @property
    def api_dialect(self) -> HTTPMetadataConsumerAPIDialect[_UM]:
        return self._api_dialect

    def dispose(self) -> None:
        self._is_disposed = True
        self._transport.dispose()
        self._logger.debug("Disposal complete.")

    def take_drain_meta(self, drain_meta: _UM) -> None:
        self._logger.info('Take drain metadata "%s".', drain_meta)
        req: Request = self._api_dialect.take_drain_meta_request_factory(
            drain_meta=drain_meta,
        )
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_take_drain_meta_response(
            response=res,
            drain_meta=drain_meta,
        )


@define(slots=True, order=False)
class HTTPMetadataSupplier(
    BaseMetadataSupplier[_DS, _DM, _EM],
    Generic[_DS, _DM, _EM],
):
    """:class:`MetadataSupplier` backed by an HTTP server."""

    _transport: HTTPTransport = field()
    _api_dialect: HTTPMetadataSupplierAPIDialect[_DS, _DM, _EM] = field()
    _valid_response_predicate: ResponsePredicate = field(
        default=if_request_accepted,
        kw_only=True,
    )

    def __attrs_post_init__(self) -> None:
        self._logger: Logger = logging.getLogger(type_fqn(self.__class__))

    @property
    def api_dialect(self) -> HTTPMetadataSupplierAPIDialect[_DS, _DM, _EM]:
        return self._api_dialect

    def dispose(self) -> None:
        self._is_disposed = True
        self._transport.dispose()
        self._logger.debug("Disposal complete.")

    def get_data_sink_meta(self) -> Iterable[_DS]:
        self._logger.info("Get data sink metadata.")
        req: Request = self._api_dialect.get_data_sink_meta_request_factory()
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_get_data_sink_meta_response(res)

    def get_data_source_meta(self) -> Iterable[_DM]:
        self._logger.info("Get data source metadata.")
        req: Request = self._api_dialect.get_data_source_meta_request_factory()
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_get_data_source_meta_response(res)

    def get_draw_meta(self, data_source_meta: _DM) -> Iterable[_EM]:
        self._logger.info(
            'Get draw metadata for data source "%s".', data_source_meta,
        )
        req: Request = self._api_dialect.get_draw_meta_request_factory(
            data_source_meta=data_source_meta,
        )
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_get_draw_meta_response(
            response=res,
            data_source_meta=data_source_meta,
        )
