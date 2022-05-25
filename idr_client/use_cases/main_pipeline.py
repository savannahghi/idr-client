from typing import Tuple

from idr_client.core import Task
from idr_client.lib import SQLMetadata


class FetchMetadataFromServer(Task[str, Tuple[SQLMetadata, SQLMetadata]]):
    """Connect to the remote server and fetch metadata."""

    def execute(self, server_url: str) -> Tuple[SQLMetadata, SQLMetadata]:
        # TODO: Add implementation. Connect to the server and fetch the
        #  metadata that describes what needs to be extracted.
        ...


class CheckChangesFromETL(Task[SQLMetadata, bool]):
    """Check a KenyaETL table for changes."""

    def execute(self, an_input: SQLMetadata) -> bool:
        # TODO: Add implementation.
        ...


class RunExtraction(Task[SQLMetadata, object]):
    """Extract data from a database."""

    def execute(self, an_input: SQLMetadata) -> object:
        # TODO: Add implementation.
        connection = None
        return an_input.as_task().execute(connection)
