"""
ETL Protocol Definition.
"""
from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Iterable
from typing import Any, Generic, TypeVar

from .base import IdentifiableDomainObject, NamedDomainObject
from .operations import (
    CleanedData,
    DataSink,
    DataSinkMetadata,
    DataSource,
    DataSourceMetadata,
    ExtractMetadata,
    ExtractProcessor,
    RawData,
    UploadMetadata,
)
from .terminals import (
    MetadataConsumer,
    MetadataSupplier,
    UploadMetadataFactory,
)

# =============================================================================
# TYPES
# =============================================================================

_CD = TypeVar("_CD", bound=CleanedData)
_DM = TypeVar("_DM", bound=DataSourceMetadata)
_DS = TypeVar("_DS", bound=DataSinkMetadata)
_EM = TypeVar("_EM", bound=ExtractMetadata)
_RD = TypeVar("_RD", bound=RawData)
_UM = TypeVar("_UM", bound=UploadMetadata)


# =============================================================================
# ETL PROTOCOL DEFINITION
# =============================================================================


class ETLProtocol(
    IdentifiableDomainObject,
    NamedDomainObject,
    Generic[_DM, _EM, _RD, _CD, _UM, _DS],
    metaclass=ABCMeta,
):
    """ETL "Service" Description.

    Defines the concrete core interfaces implementations that when combined
    constitute an ETL workflow.
    """

    @property
    @abstractmethod
    def data_sink_factory(self) -> Callable[[_DS], DataSink]:
        ...

    @property
    @abstractmethod
    def data_source_factory(self) -> Callable[[_DM], DataSource]:
        ...

    @property
    @abstractmethod
    def extract_processor_factory(
        self,
    ) -> Callable[[], ExtractProcessor[_EM, _RD, _CD]]:
        ...

    @property
    @abstractmethod
    def metadata_consumer(self) -> MetadataConsumer[_UM]:
        ...

    @property
    @abstractmethod
    def metadata_supplier(self) -> MetadataSupplier[_DS, _DM, _EM]:
        ...

    @property
    @abstractmethod
    def upload_metadata_factory(self) -> UploadMetadataFactory[_UM, _EM]:
        ...


class ETLProtocolSupplier(metaclass=ABCMeta):
    @abstractmethod
    def get_protocols(
        self,
    ) -> Iterable[ETLProtocol[Any, Any, Any, Any, Any, Any]]:
        ...
