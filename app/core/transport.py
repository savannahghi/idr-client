from abc import ABCMeta, abstractmethod
from typing import Any, Mapping, Sequence

from .domain import DataSource, DataSourceType, ExtractMetadata
from .mixins import Disposable

# =============================================================================
# TYPES
# =============================================================================

TransportOptions = Mapping[str, Any]


# =============================================================================
# TRANSPORT INTERFACE
# =============================================================================


class Transport(Disposable, metaclass=ABCMeta):
    """Represents the flow of data between an IDR Server and this app."""

    @abstractmethod
    def fetch_data_source_extracts(
        self,
        data_source_type: DataSourceType,
        data_source: DataSource,
        **options: TransportOptions,
    ) -> Sequence[ExtractMetadata]:
        """
        Fetch and return :class:`extracts <ExtractMetadata>` of the given
        :class:`data source <DataSource>` from an IDR Server.

        :param data_source_type: The data source type from which the the data
            source whose extracts are to be fetched belongs to.
        :param data_source: The data source whose extracts are to be fetched.
        :param options: Optional transport options.

        :return: A sequence of the retrieved extract metadata.

        :raise TransportClosedError: If this transport is closed.
        :raise TransportError: If an error occurs during the fetch.
        """
        ...

    @abstractmethod
    def fetch_data_sources(
        self, data_source_type: DataSourceType, **options: TransportOptions
    ) -> Sequence[DataSource]:
        """
        Fetch and return :class:`data sources <DataSource>` of the given
        :class:`data source type <DataSourceType>` from an IDR Server.

        :param data_source_type: The data source type whose data sources are to
            be fetched.
        :param options: Optional transport options.

        :return: A sequence of the retrieved data sources.

        :raise TransportClosedError: If this transport is closed.
        :raise TransportError: If an error occurs during the fetch.
        """
        ...
