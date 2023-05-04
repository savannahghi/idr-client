from abc import ABCMeta, abstractmethod
from collections.abc import Iterator
from typing import Any, Generic, Self, TypeVar

from ...mixins import Disposable
from .base import NamedDomainObject
from .metadata import (
    DataSourceMetadata,
    ExtractMetadata,
    UploadContentMetadata,
    UploadMetadata,
)

# =============================================================================
# TYPES
# =============================================================================

_CD = TypeVar("_CD", bound="CleanedData")
_DM = TypeVar("_DM", bound=DataSourceMetadata)
_EM = TypeVar("_EM", bound=ExtractMetadata)
_RD = TypeVar("_RD", bound="RawData")
_T = TypeVar("_T")
_UC = TypeVar("_UC", bound=UploadContentMetadata)
_UM = TypeVar("_UM", bound=UploadMetadata)


# =============================================================================
# OPERATION INTERFACES
# =============================================================================


class Data(Generic[_T], metaclass=ABCMeta):
    """Content resulting from the operations of the client.

    Specifically, this refers to:

    * The :class:`raw <RawData>` data extracted from a :class:`DataSource`.
    * The :class:`cleaned <CleanedData>` data returned by an
      :class:`ExtractProcessor`.

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
    Generic[_UM, _UC, _CD],
    metaclass=ABCMeta,
):
    """The final destination of extracted :class:`Data` once it is processed.

    This is a resource that consumes :class:`data<CleanedData>` once it has
    been processed and cleaned. Consumption of data can be initiated by
    calling the :meth:`start_consumption` method of a `DataSink` instance.
    """

    @abstractmethod
    def start_consumption(
        self,
        upload_metadata: _UM,
    ) -> "DataSinkStream[_UM, _UC, _CD]":
        """Start consumption of :class:`data<CleanedData>`.

        :param upload_metadata:
        :return:
        """
        ...


class DataSinkStream(Disposable, Generic[_UM, _UC, _CD], metaclass=ABCMeta):
    """
    An interface representing a series of drain *(write)* operations to a
    :class:`DataSink`.
    """

    @property
    @abstractmethod
    def data_sink(self) -> DataSink[_UM, _UC, _CD]:
        """

        :return:
        """
        ...

    @property
    @abstractmethod
    def upload_metadata(self) -> _UM:
        """

        :return:
        """
        ...

    @abstractmethod
    def consume(
        self,
        upload_content_meta: _UC,
        clean_data: _CD,
        progress: float,
    ) -> None:
        """
        Consume processed data for storage or further processing upstream.

        :param upload_content_meta: Data about this specific consumption
            operation.
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
    def start_extraction(
        self,
        extract_metadata: _EM,
    ) -> "DataSourceStream[_EM, _RD]":
        """Initiate a draw operation from this data source as defined by the
        given :class:`extraction metadata<ExtractMetadata>` and return a
        stream representing this operation.

        :param extract_metadata:
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
        return self.extract()

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
    def extract_metadata(self) -> _EM:
        """
        Return the :class:`extract metadata <ExtractMetadata>` instance that
        describes the data being drawn by this stream.

        :return: The extract metadata instance that describes the data being
            drawn.
        """
        ...

    @abstractmethod
    def extract(self) -> tuple[_RD, float]:
        """Draw data from a :class:`DataSource` and return the data and the
        progress as per the current draw.

        A negative value for the progress indicates that the stream is unbound,
        i.e. the size/length of the data being drawn in unknown. A positive
        value less than 1 indicates the current percentage of the draw. A
        positive value equal to or greater tha 1 indicates that this is the
        final draw and thus this stream will be disposed after this draw.

        After the final draw, subsequent calls to this method should raise
        `StopExtraction` to indicate that the end of the extraction has been
        reached.

        .. note::
            Even unbound streams should strive to return a value equal to or
            greater than 1 for progress on the final draw whenever possible.

        :return: The data drawn and progress of the draw.

        :raise StopExtraction: To signal the end of an extraction.
        """
        # TODO: Streams are usually unbound, so maybe return the data and a
        #  boolean to indicate whether that was the last draw or not??? This
        #  has the benefit of making the logic for determining when a stream
        #  ends easier.
        ...

    class StopExtraction(StopIteration):
        """Signal the end of an extraction."""

        ...


class ExtractProcessor(Disposable, Generic[_RD, _CD], metaclass=ABCMeta):
    """The post-extraction operation(s) to be performed on extracted data.

    This interface describes the post-extraction operation(s) to be performed
    on :class:`extracted data <RawData>` in preparation for the
    drainage/upload of the data to a :class:`data sink <DataSink>`.
    """

    @abstractmethod
    def process(self, raw_data: _RD, extract_metadata: ExtractMetadata) -> _CD:
        """

        :param raw_data:
        :param extract_metadata:
        :return:
        """
        ...


class Protocol(NamedDomainObject, metaclass=ABCMeta):
    """
    An interface that defines the kind of data being worked on and the
    operations that can be performed around that data.
    """

    @abstractmethod
    def is_supported_data_source(
        self,
        data_source_meta: DataSourceMetadata,
    ) -> bool:
        """

        :param data_source_meta:
        :return:
        """
        ...

    @abstractmethod
    def load_data_source(
        self,
        data_source_meta: DataSourceMetadata,
    ) -> DataSource:
        """

        :param data_source_meta:
        :return:
        """
        ...
