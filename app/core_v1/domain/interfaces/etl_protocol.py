"""
ETL Protocol Definition.
"""
from abc import ABCMeta, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from ...mixins import Disposable
from .base import NamedDomainObject
from .operations import (
    CleanedData,
    DataSinkMetadata,
    DataSourceMetadata,
    ExtractMetadata,
    RawData,
    UploadMetadata,
)
from .terminals import MetadataSink, MetadataSource, UploadMetadataFactory

# =============================================================================
# TYPES
# =============================================================================

_CD = TypeVar("_CD", bound=CleanedData)
_DM = TypeVar("_DM", bound=DataSourceMetadata)
_DS = TypeVar("_DS", bound=DataSinkMetadata)
_EM = TypeVar("_EM", bound=ExtractMetadata)
_RD = TypeVar("_RD", bound=RawData)
_T = TypeVar("_T")
_UM = TypeVar("_UM", bound=UploadMetadata)


# =============================================================================
# ETL PROTOCOL DEFINITION
# =============================================================================


class ETLProtocol(
    Generic[_DM, _EM, _RD, _CD, _UM, _DS],
    NamedDomainObject,
    Disposable,
    metaclass=ABCMeta,
):
    """ETL "Service" Description.

    Defines the concrete core interfaces implementations that when combined
    constitute an ETL workflow.
    """

    @property
    @abstractmethod
    def metadata_sinks(self) -> Iterable[MetadataSink[_UM, _EM]]:
        ...

    @property
    @abstractmethod
    def metadata_sources(self) -> Iterable[MetadataSource[_DS, _DM, _EM]]:
        ...

    @property
    @abstractmethod
    def upload_metadata_factory(self) -> UploadMetadataFactory[_UM, _EM]:
        ...
