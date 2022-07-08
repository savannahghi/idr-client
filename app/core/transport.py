from abc import ABCMeta, abstractmethod
from typing import Any, Mapping

from .domain import DataSource, DataSourceType, ExtractMetadata

# =============================================================================
# TYPES
# =============================================================================

TransportOptions = Mapping[str, Any]


# =============================================================================
# TRANSPORT INTERFACE
# =============================================================================


class Transport(metaclass=ABCMeta):
    """Represents the flow of data between an IDR Server this app."""

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def fetch_data_source_extracts(
        self, data_source: DataSource, **options: TransportOptions
    ) -> Mapping[str, ExtractMetadata]:
        ...

    @abstractmethod
    def fetch_data_sources(
        self, data_source_type: DataSourceType, **options: TransportOptions
    ) -> Mapping[str, DataSource]:
        ...
