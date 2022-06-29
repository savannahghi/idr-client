from typing import Callable, Mapping, Optional

from app.core import DataSource, ExtractMetadata, Transport, TransportOptions


class HTTPTransport(Transport):
    """
    An implementation of the transport interface that uses the HTTP protocol
    for data transmission.
    """

    def flush(
            self,
            timeout: Optional[float] = None,
            callback: Optional[Callable[[bool, Optional[str]], None]] = None
    ) -> None:
        raise NotImplementedError('"flush" must be implemented')

    def fetch_data_source_extract_metadata(
            self,
            data_source_id: str,
            **options: TransportOptions
    ) -> Mapping[str, ExtractMetadata]:
        # TODO: Add implementation.
        return dict()

    def fetch_data_sources(
            self,
            **options: TransportOptions
    ) -> Mapping[str, DataSource]:
        # TODO: Add implementation.
        return dict()
