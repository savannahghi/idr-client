from abc import ABCMeta, abstractmethod
from collections.abc import Iterable, Mapping
from typing import Any, Generic, TypeVar

from ...mixins import Disposable
from .base import NamedDomainObject
from .metadata import (
    DataSinkMetadata,
    DataSourceMetadata,
    ExtractMetadata,
    UploadMetadata,
)

# =============================================================================
# TYPES
# =============================================================================


_DM = TypeVar("_DM", bound=DataSourceMetadata)
_DS = TypeVar("_DS", bound=DataSinkMetadata)
_EM = TypeVar("_EM", bound=ExtractMetadata)
_UM = TypeVar("_UM", bound=UploadMetadata)

# =============================================================================
# PIPELINE TERMINAL INTERFACES
# =============================================================================


class MetadataConsumer(
    NamedDomainObject,
    Disposable,
    Generic[_UM],
    metaclass=ABCMeta,
):
    """Upload/Drain related metadata consumer.

    An interface representing entities that take/accept metadata relating to
    uploaded/drained data.
    """

    @abstractmethod
    def take_upload_meta(self, upload_meta: _UM) -> None:
        """

        :param upload_meta:
        :return:
        """
        ...


class MetadataSupplier(
    NamedDomainObject,
    Disposable,
    Generic[_DS, _DM, _EM],
    metaclass=ABCMeta,
):
    """Known metadata producer/provider.

    An interface representing entities that serve/produce metadata describing
    what data is to be drawn/extracted and from where, and finally where that
    data should be drained/uploaded to.
    """

    @abstractmethod
    def get_data_sink_meta(self) -> Iterable[_DS]:
        """

        :return:
        """
        ...

    @abstractmethod
    def get_data_source_meta(self) -> Iterable[_DM]:
        """

        :return:
        """
        ...

    @abstractmethod
    def get_extract_meta(self, data_source_meta: _DM) -> Iterable[_EM]:
        """

        :return:
        """
        ...


class UploadMetadataFactory(Disposable, Generic[_UM, _EM], metaclass=ABCMeta):
    """Create new :class:`UploadMetadata` instances on demand.

    This class enables different ETLWorkflow definitions to provide a hook for
    initializing :class:`UploadMetadata` instances that they work with.
    """

    @abstractmethod
    def new_upload_meta(
        self,
        extract_meta: _EM,
        **kwargs: Mapping[str, Any],
    ) -> _UM:
        """

        :param extract_meta:
        :param kwargs:

        :return:
        """
        ...