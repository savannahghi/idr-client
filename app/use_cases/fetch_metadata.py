from logging import getLogger
from typing import Mapping

from app.core import DataSource, ExtractMetadata, Task, Transport

# =============================================================================
# CONSTANTS
# =============================================================================

LOGGER = getLogger(__name__)


# =============================================================================
# TASKS
# =============================================================================


class FetchDataSources(Task[None, Mapping[str, DataSource]]):
    def __init__(self, transport: Transport):
        self._transport: Transport = transport

    def execute(self, an_input: None) -> Mapping[str, DataSource]:
        # TODO: Add a proper implementation
        LOGGER.info("Fetching data sources.")
        return self._transport.fetch_data_sources()


class FetchExtractMetadata(
    Task[Mapping[str, DataSource], Mapping[str, ExtractMetadata]]
):
    def __init__(self, transport: Transport):
        self._transport: Transport = transport

    def execute(
        self, an_input: Mapping[str, DataSource]
    ) -> Mapping[str, ExtractMetadata]:
        # TODO: Add a proper implementation
        LOGGER.info("Fetching extract metadata.")
        return self._transport.fetch_data_source_extract_metadata("")
