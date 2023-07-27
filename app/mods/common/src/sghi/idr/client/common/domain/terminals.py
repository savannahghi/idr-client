from collections.abc import Iterable
from typing import Any, Self

from sghi.idr.client.core.domain import (
    BaseDrainMetadataFactory,
    BaseMetadataConsumer,
    CleanedData,
    DataSink,
    DataSinkSelector,
    DrainMetadata,
    DrawMetadata,
)

from .metadata import SimpleDrainMetadata


class NullMetadataConsumer(BaseMetadataConsumer[Any]):
    """:class:`MetadataConsumer` that discards all the :class:`DrainMetadata`
    it receives.
    """

    def dispose(self) -> None:
        self._is_disposed = True

    def take_drain_meta(self, drain_meta: DrainMetadata) -> None:
        """Discard the given :class:`DrainMetadata`

        :param drain_meta: `DrainMetadata` supplied to this consumer.

        :returns: None.
        """
        ...

    @classmethod
    def of(
        cls,
        name: str = "NullMetadataConsumer",
        description: str | None = "Discards all received drain metadata.",
    ) -> Self:
        return cls(name=name, description=description)  # pyright: ignore


class SelectAllDataSinkSelector(DataSinkSelector[Any, Any, Any, Any]):
    """:class:`DataSinkSelector` that selects all the given
    :class:`data sinks<DataSink>`.
    """

    def select(
        self,
        data_sinks: Iterable[DataSink[Any, Any, Any]],
        drain_meta: DrainMetadata,
        clean_data: CleanedData,
    ) -> Iterable[DataSink[Any, Any, Any]]:
        return data_sinks


class SelectNoneDataSinkSelector(DataSinkSelector[Any, Any, Any, Any]):
    """:class:`DataSinkSelector` that rejects all the given
    :class:`data sinks<DataSink>`.
    """

    def select(
        self,
        data_sinks: Iterable[DataSink[Any, Any, Any]],
        drain_meta: DrainMetadata,
        clean_data: CleanedData,
    ) -> Iterable[DataSink[Any, Any, Any]]:
        return ()


class SimpleDrainMetadataFactory(BaseDrainMetadataFactory[Any, Any]):
    """:class:`DrainMetadataFactory` that creates and returns new instances
    of :class:`SimpleDrainMetadata`.
    """

    def new_drain_meta(self, draw_meta: DrawMetadata) -> DrainMetadata:
        """Create and return a new `SimpleDrainMetadata` instance derived from
        the given :class:`DrawMetadata` instance.

        .. note::
            Internally, this method uses the factory method
            :meth:`SimpleDrainMetadata.of_draw_metadata`.

        :param draw_meta: A source `DrawMetadata` from which to derive a
            new `SimpleDrainMetadata` instance.

        :return: A `SimpleDrainMetadata` instance derived from the given
            `DrawMetadata` instance.
        """
        return SimpleDrainMetadata.of_draw_metadata(draw_metadata=draw_meta)

    def dispose(self) -> None:
        self._is_disposed = True
