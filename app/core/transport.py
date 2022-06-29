from abc import ABCMeta, abstractmethod
from typing import Any, Callable, Mapping, Optional

from .domain import DataSource, ExtractMetadata

TransportOptions = Mapping[str, Any]


class Transport(metaclass=ABCMeta):
    """Represents the flow of data between an IDR Server this app."""

    @abstractmethod
    def flush(
            self,
            timeout: Optional[float] = None,
            callback: Optional[Callable[[bool, Optional[str]], None]] = None
    ) -> None:
        ...

    @abstractmethod
    def fetch_data_source_extract_metadata(
            self,
            data_source_id: str,
            **options: TransportOptions
    ) -> Mapping[str, ExtractMetadata]:
        ...

    @abstractmethod
    def fetch_data_sources(
            self,
            **options: TransportOptions
    ) -> Mapping[str, DataSource]:
        ...
