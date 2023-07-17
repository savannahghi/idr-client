from abc import ABCMeta, abstractmethod
from collections.abc import Iterable
from typing import Generic, TypeVar

from ...mixins import Disposable
from .base import NamedDomainObject
from .metadata import (
    DataSinkMetadata,
    DataSourceMetadata,
    DrainMetadata,
    DrawMetadata,
)
from .operations import CleanedData, DataSink

# =============================================================================
# TYPES
# =============================================================================


_CD = TypeVar("_CD", bound=CleanedData)
_DM = TypeVar("_DM", bound=DataSourceMetadata)
_DS = TypeVar("_DS", bound=DataSinkMetadata)
_EM = TypeVar("_EM", bound=DrawMetadata)
_UM = TypeVar("_UM", bound=DrainMetadata)

# =============================================================================
# PIPELINE TERMINAL INTERFACES
# =============================================================================


class DataSinkSelector(Generic[_DS, _DM, _CD, _UM], metaclass=ABCMeta):
    """Pick the :class:`data sinks<DataSink>` to drain :class:`CleanedData` to.

    This allows an `ETLProtocol` to route data to specific data sinks.
    """

    @abstractmethod
    def select(
        self,
        data_sinks: Iterable[DataSink[_DS, _DM, _CD]],
        drain_meta: _UM,
        clean_data: _CD,
    ) -> Iterable[DataSink[_DS, _DM, _CD]]:
        """Pick the target :class:`data sinks<DataSink>` to drain the given
        data.

        A selector can return an empty iterable to indicate that the data
        shouldn't be drained to any data sink.

        :param data_sinks: All available data sinks.
        :param drain_meta: The drain metadata associated with the data being
            drained.
        :param clean_data: The data being drained.

        :return: The data sinks to drain the given data to.
        """
        ...


class DrainMetadataFactory(Disposable, Generic[_UM, _EM], metaclass=ABCMeta):
    """Create new :class:`DrawMetadata` instances on demand.

    This class enables different `ETLProtocol` instances to provide a hook for
    initializing :class:`DrawMetadata` instances that they work with.
    """

    @abstractmethod
    def new_drain_meta(self, draw_meta: _EM) -> _UM:
        """

        :param draw_meta:

        :return:
        """
        ...


class MetadataConsumer(
    NamedDomainObject,
    Disposable,
    Generic[_UM],
    metaclass=ABCMeta,
):
    """Drain related metadata consumer.

    An interface representing entities that take/accept metadata relating to
    uploaded/drained data.
    """

    @abstractmethod
    def take_drain_meta(self, drain_meta: _UM) -> None:
        """

        :param drain_meta:
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
    def get_draw_meta(self, data_source_meta: _DM) -> Iterable[_EM]:
        """

        :return:
        """
        ...
