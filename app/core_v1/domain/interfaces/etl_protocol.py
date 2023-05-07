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
    DataSink,
    DataSinkMetadata,
    DataSource,
    DataSourceMetadata,
    ExtractMetadata,
    RawData,
    UploadMetadata,
)
from .terminals import MetadataSink, MetadataSource

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
    """
    A definition of the kinds of supported operations and concrete
    implementations needed to facilitate an ETL Workflow.
    """

    @property
    @abstractmethod
    def metadata_sink(self) -> MetadataSink:
        # TODO: Brainstorm
        #  Return a single sink so that it can be used to create new
        #  UploadMetadata instances.
        ...

    @property
    @abstractmethod
    def metadata_sources(self) -> Iterable[MetadataSource]:
        ...

    @abstractmethod
    def pick_drain_target(self, upload_meta: _UM) -> DataSink[_DS, _UM, _CD]:
        """

        :param upload_meta:

        :return:
        """
        ...

    @abstractmethod
    def pick_draw_target(self, extract_meta: _EM) -> DataSource[_DM, _EM, _RD]:
        """

        :param extract_meta:

        :return:
        """
        ...
