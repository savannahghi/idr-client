from logging import getLogger
from typing import Dict, Mapping, Sequence

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
# TASKS
# =============================================================================


class DoFetchDataSourceTypeSources(
    Task[DataSourceType, Mapping[str, DataSource]]
):
    """Fetches all the data sources of a given data source type."""

    def __init__(self, data_source_type: DataSourceType):
        self._data_source_type: DataSourceType = data_source_type

    def execute(self, an_input: Transport) -> Mapping[str, DataSource]:
        _LOGGER.info(
            'Fetching data sources for data source type="%s".',
            str(self._data_source_type),
        )
        dss: Mapping[str, DataSource] = an_input.fetch_data_sources(
            self._data_source_type
        )
        self._data_source_type.data_sources = dss
        return dss


class DoFetchDataSourceExtracts(
    Task[DataSource, Mapping[str, ExtractMetadata]]
):
    """Fetch all the extract metadata of a given data source."""

    def __init__(self, data_source: DataSource):
        self._data_source: DataSource = data_source

    def execute(self, an_input: Transport) -> Mapping[str, ExtractMetadata]:
        _LOGGER.info(
            'Fetching extract metadata for data source="%s".',
            str(self._data_source),
        )
        em: Mapping[str, ExtractMetadata]
        em = an_input.fetch_data_source_extracts(self._data_source)
        self._data_source.extract_metadata = em
        return em


class FetchDataSources(Task[Transport, Mapping[str, DataSource]]):
    """
    Fetch all the :class:`data sources <DataSource>` for the given
    :class:`data source types <DataSourceType>`.
    """

    def __init__(self, transport: Transport):
        self._transport: Transport = transport

    def execute(
        self, an_input: Mapping[str, DataSourceType]
    ) -> Mapping[str, DataSource]:
        _LOGGER.info("Fetching data sources.")
        executor: ConcurrentExecutor[
            Transport, Sequence[Mapping[str, DataSource]]
        ] = ConcurrentExecutor(
            *self._data_source_types_to_tasks(an_input), initial_value=list()
        )
        sources: Sequence[Mapping[str, DataSource]] = executor(  # noqa
            self._transport
        )
        output: Dict[str, DataSource] = dict()
        # Flatten nested data
        for _sources in sources:
            output.update(_sources)
        return output

    @staticmethod
    def _data_source_types_to_tasks(
        data_source_types: Mapping[str, DataSourceType]
    ) -> Sequence[DoFetchDataSourceTypeSources]:
        return tuple(
            (
                DoFetchDataSourceTypeSources(
                    data_source_type=_data_source_type
                )
                for _data_source_type in data_source_types.values()
            )
        )


class FetchExtractMetadata(
    Task[Mapping[str, DataSource], Mapping[str, ExtractMetadata]]
):
    """
    Fetch all :class:`extract metadata <ExtractMetadata>` for the given
    :class:`data sources <DataSource>`.
    """

    def __init__(self, transport: Transport):
        self._transport: Transport = transport

    def execute(
        self, an_input: Mapping[str, DataSource]
    ) -> Mapping[str, ExtractMetadata]:
        _LOGGER.info("Fetching extract metadata.")
        executor: ConcurrentExecutor[
            Transport, Sequence[Mapping[str, ExtractMetadata]]
        ] = ConcurrentExecutor(
            *self._data_sources_to_tasks(an_input), initial_value=list()
        )
        extracts: Sequence[Mapping[str, ExtractMetadata]] = executor(  # noqa
            self._transport
        )
        output: Dict[str, ExtractMetadata] = dict()
        # Flatten nested data
        for _extracts in extracts:
            output.update(_extracts)
        return output

    @staticmethod
    def _data_sources_to_tasks(
        data_sources: Mapping[str, DataSource]
    ) -> Sequence[DoFetchDataSourceExtracts]:
        return tuple(
            (
                DoFetchDataSourceExtracts(data_source=_data_source)
                for _data_source in data_sources.values()
            )
        )
