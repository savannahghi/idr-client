from abc import ABCMeta, abstractmethod
from collections.abc import Iterator
from typing import Any, Generic, Self, TypeVar

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

_CD = TypeVar("_CD", bound="CleanedData")
_DM = TypeVar("_DM", bound=DataSourceMetadata)
_DS = TypeVar("_DS", bound=DataSinkMetadata)
_EM = TypeVar("_EM", bound=DrawMetadata)
_RD = TypeVar("_RD", bound="RawData")
_T = TypeVar("_T")
_UM = TypeVar("_UM", bound=DrainMetadata)


# =============================================================================
# OPERATION INTERFACES
# =============================================================================


class Data(Generic[_T], metaclass=ABCMeta):
    """Content resulting from the operations of the client.

    Specifically, this refers to:

    * The :class:`raw <RawData>` data drawn from a :class:`DataSource`.
    * The :class:`cleaned <CleanedData>` data returned by an
      :class:`DataProcessor`.

    This interface defines one read-only property :attr:`content` that returns
    the actual constituent material represented by a given instance.
    """

    @property
    @abstractmethod
    def content(self) -> _T:
        """Return the actual constituent material represented by this instance.

        :return: the actual constituent material represented by this instance.
        """
        ...

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Return a MIME type representing the type of this data.

        :return: the MIME type representing the of this data.
        """
        ...

    @property
    @abstractmethod
    def index(self) -> int:
        """Return an integer representing the offset of this data since the
        draw or drain was started.

        For cases where this is not available, or where the ordering of the
        data is not important, a value of -1 should be returned instead.

        :return: the offset of this data since the draw or drain was started.
        """


class CleanedData(Generic[_T], Data[_T], metaclass=ABCMeta):
    """:class:`RawData` after it is processed.

    Represents `RawData` that has already been processed and is ready to be
    drained to a :class:`data sink <DataSink>`.
    """

    ...


class RawData(Generic[_T], Data[_T], metaclass=ABCMeta):
    """Data drawn from a :class:`DataSource` but before it is processed."""

    ...


class DataSink(
    NamedDomainObject,
    Disposable,
    Generic[_DS, _UM, _CD],
    metaclass=ABCMeta,
):
    """The final destination of extracted :class:`Data` once it is processed.

    This is a resource that consumes :class:`data<CleanedData>` once it has
    been processed and cleaned. Consumption of data can be initiated by
    calling the :meth:`start_consumption` method of a `DataSink` instance.
    """

    @abstractmethod
    def start_drain(self, drain_metadata: _UM) -> "DataSinkStream[_UM, _CD]":
        """Start consumption of :class:`clean data<CleanedData>`.

        :param drain_metadata: Information about the data to be drained to the
            sink.

        :return: A `DataSinkStream` representing the drain operation.
        """
        ...

    @classmethod
    @abstractmethod
    def from_data_sink_meta(cls, data_sink_meta: _DS) -> Self:
        """Return `DataSink` instance given a :class:`DataSinkMetadata`.

        :param data_sink_meta: A `DataSinkMetadata` instance describing a
            `DataSink`.

        :return: The `DataSink` instance described by the given
            `DataSinkMetadata` instance.
        """
        ...


class DataSinkStream(Disposable, Generic[_UM, _CD], metaclass=ABCMeta):
    """
    An interface representing a series of drain *(write)* operations to a
    :class:`DataSink`.
    """

    @property
    @abstractmethod
    def data_sink(self) -> DataSink[Any, _UM, _CD]:
        """

        :return:
        """
        ...

    @property
    @abstractmethod
    def drain_metadata(self) -> _UM:
        """

        :return:
        """
        ...

    @abstractmethod
    def drain(self, clean_data: _CD, progress: float) -> None:
        """
        Consume processed data for storage or further processing downstream.

        :param clean_data: Data that is already processed and ready for
            consumption downstream.
        :param progress: Indicate the current drain progress.
        """
        ...


class DataSource(
    NamedDomainObject,
    Disposable,
    Generic[_DM, _EM, _RD],
    metaclass=ABCMeta,
):
    """An interface representing an entity that contains data of interest."""

    @abstractmethod
    def start_draw(self, draw_metadata: _EM) -> "DataSourceStream[_EM, _RD]":
        """Initiate a draw operation from this data source as defined by the
        given :class:`draw metadata<ExtractMetadata>` and return a stream
        representing this operation.

        :param draw_metadata:
        :return:
        """
        ...

    @classmethod
    @abstractmethod
    def from_data_source_meta(cls, data_source_meta: _DM) -> Self:
        """

        :param data_source_meta:
        :return:
        """
        ...


class DataSourceStream(
    Disposable,
    Iterator[tuple[_RD, float]],
    Generic[_EM, _RD],
    metaclass=ABCMeta,
):
    """
    An interface representing a series of draw *(read)* operations from a
    :class:`DataSource`.
    """

    def __iter__(self) -> Iterator[tuple[_RD, float]]:
        return self

    def __next__(self) -> tuple[_RD, float]:
        return self.draw()

    @property
    @abstractmethod
    def data_source(self) -> DataSource[Any, _EM, _RD]:
        """
        Return the :class:`data source <DataSource>` instance that this
        stream is drawing from.

        :return: The data source instance that this stream is drawing from.
        """
        ...

    @property
    @abstractmethod
    def draw_metadata(self) -> _EM:
        """
        Return the :class:`draw metadata <ExtractMetadata>` instance that
        describes the data being drawn by this stream.

        :return: The draw metadata instance that describes the data being
            drawn.
        """
        ...

    @abstractmethod
    def draw(self) -> tuple[_RD, float]:
        """Extract data from a :class:`DataSource` and return the data and the
        progress as per the current draw.

        A negative value for the progress indicates that the stream is unbound,
        i.e. the size/length of the data being drawn in unknown. A positive
        value less than 1 indicates the current percentage of the draw. A
        positive value equal to or greater tha 1 indicates that this is the
        final draw and thus this stream will be disposed after this draw.

        After the final draw, subsequent calls to this method should raise
        `StopDraw` to indicate that the end of the extraction has been reached.

        .. note::
            Even unbound streams should strive to return a value equal to or
            greater than 1 for progress on the final draw whenever possible.

        :return: The data drawn and progress of the draw.

        :raise StopDraw: To signal the end of a draw.
        """
        ...

    class StopDraw(StopIteration):
        """Signal the end of a draw.

        All data described by a :class:`DrawMetadata` instance has been drawn.
        """

        ...


class DataProcessor(Disposable, Generic[_EM, _RD, _CD], metaclass=ABCMeta):
    """The post-extraction operation(s) to be performed on drawn data.

    This interface describes the post-extraction operation(s) to be performed
    on :class:`drawn data <RawData>` in preparation for the drainage of the
    data to a :class:`data sink <DataSink>`.
    """

    @abstractmethod
    def process(self, raw_data: _RD, draw_metadata: _EM) -> _CD:
        """

        :param raw_data:
        :param draw_metadata:
        :return:
        """
        ...
