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


class MetadataSink(
    NamedDomainObject,
    Disposable,
    Generic[_UM, _EM],
    metaclass=ABCMeta,
):
    """Upload(s) related metadata consumer.

    An interface representing entities that consume metadata relating to
    uploaded data.
    """

    # TODO: Think🤔 about where are UploadMetadata ID's going to come from?
    @abstractmethod
    def consume_upload_meta(self, upload_meta: _UM) -> None:
        """

        :param upload_meta:
        :return:
        """
        ...

    @abstractmethod
    def init_upload_metadata_consumption(
        self,
        extract_metadata: _EM,
        content_type: str,
        **kwargs: Mapping[str, Any],
    ) -> _UM:
        """

        :param extract_metadata:
        :param content_type:
        :return:
        """
        ...


class MetadataSource(
    NamedDomainObject,
    Disposable,
    Generic[_DS, _DM, _EM],
    metaclass=ABCMeta,
):
    """Extract(s) related metadata producer/provider.

    An interface representing entities that serve/produce metadata describing
    what data is to be extracted and from where.
    """

    @abstractmethod
    def provide_data_sink_meta(self) -> Iterable[_DS]:
        """

        :return:
        """
        ...

    @abstractmethod
    def provide_data_source_meta(self) -> Iterable[_DM]:
        """

        :return:
        """
        ...

    @abstractmethod
    def provide_extract_meta(self, data_source: _DM) -> Iterable[_EM]:
        """

        :return:
        """
        ...
