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

# =============================================================================
# TYPES
# =============================================================================


_DM = TypeVar("_DM", bound=DataSourceMetadata)
_DS = TypeVar("_DS", bound=DataSinkMetadata)
_EM = TypeVar("_EM", bound=DrawMetadata)
_UM = TypeVar("_UM", bound=DrainMetadata)

# =============================================================================
# PIPELINE TERMINAL INTERFACES
# =============================================================================


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
