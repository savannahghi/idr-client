import logging
from collections.abc import Iterable, Mapping
from logging import Logger
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from attrs import define, field
from sghi.idr.client.core.domain import (
    BaseMetadataConsumer,
    BaseMetadataSupplier,
    BaseUploadMetadataFactory,
    DataSinkMetadata,
    DataSourceMetadata,
    ExtractMetadata,
    UploadMetadata,
)

from ..lib import (
    HTTPMetadataConsumerAPIDialect,
    HTTPMetadataSupplierAPIDialect,
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
class HTTPMetadataConsumer(BaseMetadataConsumer[_UM], Generic[_UM]):
    """:class:`MetadataConsumer` backed by an HTTP server."""

    _transport: HTTPTransport = field()
    _api_dialect: HTTPMetadataConsumerAPIDialect[_UM] = field()
    _valid_response_predicate: ResponsePredicate = field(
        default=if_request_accepted,
        kw_only=True,
    )

    def __attrs_post_init__(self) -> None:
        self._logger: Logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__qualname__}",
        )

    @property
    def api_dialect(self) -> HTTPMetadataConsumerAPIDialect[_UM]:
        return self._api_dialect

    def dispose(self) -> None:
        self._is_disposed = True
        self._transport.dispose()
        self._logger.debug("Disposal complete.")

    def take_upload_meta(self, upload_meta: _UM) -> None:
        self._logger.info('Accept upload metadata "%s".', upload_meta)
        req: Request = self._api_dialect.take_upload_meta_request_factory(
            upload_meta=upload_meta,
        )
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_take_upload_meta_response(
            response=res,
            upload_meta=upload_meta,
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
        self._logger: Logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__qualname__}",
        )

    @property
    def api_dialect(self) -> HTTPMetadataSupplierAPIDialect[_DS, _DM, _EM]:
        return self._api_dialect

    def dispose(self) -> None:
        self._is_disposed = True
        self._transport.dispose()
        self._logger.debug("Disposal complete.")

    def get_data_sink_meta(self) -> Iterable[_DS]:
        self._logger.info("Provide data sink metadata.")
        req: Request = self._api_dialect.get_data_sink_meta_request_factory()
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_get_data_sink_meta_response(res)

    def get_data_source_meta(self) -> Iterable[_DM]:
        self._logger.info("Provide data source metadata.")
        req: Request = self._api_dialect.get_data_source_meta_request_factory()
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_get_data_source_meta_response(res)

    def get_extract_meta(
        self,
        data_source_meta: _DM,
    ) -> Iterable[_EM]:
        self._logger.info(
            'Provide extract metadata for data source "%s".',
            data_source_meta,
        )
        req: Request = self._api_dialect.get_extract_meta_request_factory(
            data_source_meta=data_source_meta,
        )
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_get_extract_meta_response(
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

    def __attrs_post_init__(self) -> None:
        self._logger: Logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__qualname__}",
        )

    @property
    def api_dialect(self) -> HTTPUploadMetadataFactoryAPIDialect[_UM, _EM]:
        return self._api_dialect

    def dispose(self) -> None:
        self._is_disposed = True
        self._transport.dispose()
        self._logger.debug("Disposal complete.")

    def new_upload_meta(
        self,
        extract_meta: _EM,
        **kwargs: Mapping[str, Any],
    ) -> _UM:
        self._logger.info(
            'Initialize a new UploadMetadata instance of extract meta "%s".',
            extract_meta,
        )
        req: Request = self._api_dialect.new_upload_meta_request_factory(
            extract_meta=extract_meta,
            **kwargs,
        )
        res: Response = self._transport.make_request(
            request=req,
            valid_response_predicate=self._valid_response_predicate,
        )
        return self._api_dialect.handle_new_upload_meta_response(
            response=res,
            extract_meta=extract_meta,
            **kwargs,
        )
