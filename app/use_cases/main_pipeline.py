from typing import Mapping

from app.core import ExtractMetadata, Task, Transport
from app.lib import Pipeline

from .fetch_metadata import FetchDataSources, FetchExtractMetadata


class FetchMetadata(Pipeline[None, Mapping[str, ExtractMetadata]]):
    """Connect to the remote server and fetch metadata."""

    def __init__(self, transport: Transport):
        super().__init__(
            FetchDataSources(transport=transport),
            FetchExtractMetadata(transport=transport),
        )


class RunExtraction(Task[Mapping[str, ExtractMetadata], object]):
    """Extract data from a database."""

    def execute(self, an_input: Mapping[str, ExtractMetadata]) -> object:
        # TODO: Add proper implementation
        return object()


class ProcessExtracts(Task[object, object]):
    """Perform any required processing on the extracted data."""

    def execute(self, an_input: object) -> object:
        # TODO: Add proper implementation
        return an_input


class UploadExtracts(Task[object, object]):
    """Upload the extracted metadata to the remote server."""

    def __init__(self, transport: Transport):
        self._transport: Transport = transport

    def execute(self, an_input: object) -> object:
        # TODO: Add proper implementation
        return an_input
