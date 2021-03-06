from itertools import chain
from logging import getLogger
from typing import Iterable, Mapping, Sequence

from app.core import (
    DataSource,
    DataSourceType,
    ExtractMetadata,
    Task,
    Transport,
)
from app.lib import ConcurrentExecutor

# =============================================================================
# CONSTANTS
# =============================================================================


_LOGGER = getLogger(__name__)


# =============================================================================
# HELPER TASKS
# =============================================================================


class DoFetchDataSourceTypeSources(Task[DataSourceType, Sequence[DataSource]]):
    """Fetches all the data sources of a given data source type."""

    def __init__(self, data_source_type: DataSourceType):
        self._data_source_type: DataSourceType = data_source_type

    def execute(self, an_input: Transport) -> Sequence[DataSource]:
        _LOGGER.info(
            'Fetching data sources for data source type="%s".',
            str(self._data_source_type),
        )
        data_sources: Sequence[DataSource] = an_input.fetch_data_sources(
            self._data_source_type
        )
        data_source_type_sources: Mapping[str, DataSource] = {
            _data_source.id: _data_source for _data_source in data_sources
        }
        self._data_source_type.data_sources = data_source_type_sources
        return data_sources


class DoFetchDataSourceExtracts(Task[DataSource, Sequence[ExtractMetadata]]):
    """Fetch all the extract metadata of a given data source."""

    def __init__(self, data_source: DataSource):
        self._data_source: DataSource = data_source

    def execute(self, an_input: Transport) -> Sequence[ExtractMetadata]:
        _LOGGER.info(
            'Fetching extract metadata for data source="%s".',
            str(self._data_source),
        )
        extracts: Sequence[ExtractMetadata]
        extracts = an_input.fetch_data_source_extracts(
            data_source_type=self._data_source.data_source_type,
            data_source=self._data_source,
        )
        data_source_extracts: Mapping[str, ExtractMetadata] = {
            _extract.id: _extract for _extract in extracts
        }
        self._data_source.extract_metadata = data_source_extracts
        return extracts


# =============================================================================
# MAIN TASKS
# =============================================================================


class FetchDataSources(Task[Sequence[DataSourceType], Sequence[DataSource]]):
    """
    Fetch all the :class:`data sources <DataSource>` for the given
    :class:`data source types <DataSourceType>`.
    """

    def __init__(self, transport: Transport):
        self._transport: Transport = transport

    def execute(
        self, an_input: Sequence[DataSourceType]
    ) -> Sequence[DataSource]:
        _LOGGER.info("Fetching data sources.")
        executor: ConcurrentExecutor[
            Transport, Sequence[Sequence[DataSource]]
        ] = ConcurrentExecutor(
            *self._data_source_types_to_tasks(an_input), initial_value=list()
        )
        data_sources: Sequence[Sequence[DataSource]]
        data_sources = executor(self._transport)  # noqa
        return tuple(chain.from_iterable(data_sources))

    @staticmethod
    def _data_source_types_to_tasks(
        data_source_types: Iterable[DataSourceType],
    ) -> Sequence[DoFetchDataSourceTypeSources]:
        return tuple(
            (
                DoFetchDataSourceTypeSources(
                    data_source_type=_data_source_type
                )
                for _data_source_type in data_source_types
            )
        )


class FetchExtractMetadata(
    Task[Sequence[DataSource], Sequence[ExtractMetadata]]
):
    """
    Fetch all :class:`extract metadata <ExtractMetadata>` for the given
    :class:`data sources <DataSource>`.
    """

    def __init__(self, transport: Transport):
        self._transport: Transport = transport
        super().__init__()

    def execute(
        self, an_input: Sequence[DataSource]
    ) -> Sequence[ExtractMetadata]:
        _LOGGER.info("Fetching extract metadata.")
        executor: ConcurrentExecutor[
            Transport, Sequence[Sequence[ExtractMetadata]]
        ] = ConcurrentExecutor(
            *self._data_sources_to_tasks(an_input), initial_value=list()
        )
        extracts: Sequence[Sequence[ExtractMetadata]]
        extracts = executor(self._transport)  # noqa
        return tuple(chain.from_iterable(extracts))

    @staticmethod
    def _data_sources_to_tasks(
        data_sources: Iterable[DataSource],
    ) -> Sequence[DoFetchDataSourceExtracts]:
        return tuple(
            (
                DoFetchDataSourceExtracts(data_source=_data_source)
                for _data_source in data_sources
            )
        )
