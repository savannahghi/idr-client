from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from typing import Any

from attrs import define, field

from app.core_v1.domain import BaseDataSinkMetadata

from ..lib import HTTPDataSinkAPIDialect, if_request_accepted
from ..typings import HTTPTransportFactory, ResponsePredicate

# =============================================================================
# BASE METADATA CLASSES
# =============================================================================


@define(slots=False)
class BaseHTTPDataSinkMetadata(BaseDataSinkMetadata, metaclass=ABCMeta):
    """Base descriptor for :class:`HTTP data sinks<DataSinkMetadata>`."""

    @property
    @abstractmethod
    def transport_factory(self) -> HTTPTransportFactory:
        ...

    @property
    @abstractmethod
    def api_dialect_factory(self) -> Callable[[], HTTPDataSinkAPIDialect[Any]]:
        ...

    @property
    @abstractmethod
    def valid_response_predicate(self) -> ResponsePredicate:
        ...


# =============================================================================
# CONCRETE METADATA IMPLEMENTATIONS
# =============================================================================


@define(slots=True)
class SimpleHTTPDataSinkMetadata(BaseHTTPDataSinkMetadata):
    """Simple `HTTPDataSink` descriptor."""

    _transport_factory: HTTPTransportFactory = field()
    _api_dialect_factory: Callable[[], HTTPDataSinkAPIDialect[Any]] = field()
    _valid_response_predicate: ResponsePredicate = field(
        default=if_request_accepted,
        kw_only=True,
    )

    @property
    def api_dialect_factory(self) -> Callable[[], HTTPDataSinkAPIDialect[Any]]:
        return self._api_dialect_factory

    @property
    def transport_factory(self) -> HTTPTransportFactory:
        return self._transport_factory

    @property
    def valid_response_predicate(self) -> ResponsePredicate:
        return self._valid_response_predicate
