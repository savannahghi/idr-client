from itertools import chain, groupby, product
from logging import getLogger
from typing import Iterable, Mapping, Sequence, Tuple

from app.core import (
    DataSource,
    DataSourceType,
    ExtractMetadata,
    Task,
    Transport,
)
from app.lib import ConcurrentExecutor, Consumer

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
        data_sources: Sequence[DataSource] = an_input.fetch_data_sources(
            self._data_source_type
        )
        data_source_type_sources: Mapping[str, DataSource] = {
            _data_source.id: _data_source for _data_source in data_sources
        }
        self._data_source_type.data_sources = data_source_type_sources
        return data_source_type_sources


class DoFetchDataSourceExtracts(
    Task[DataSource, Mapping[str, ExtractMetadata]]
):
    """Fetch all the extract metadata of a given data source."""

    def __init__(
        self, data_source_type: DataSourceType, data_source: DataSource
    ):
        self._data_source_type: DataSourceType = data_source_type
        self._data_source: DataSource = data_source

    def execute(self, an_input: Transport) -> Mapping[str, ExtractMetadata]:
        _LOGGER.info(
            'Fetching extract metadata for data source="%s".',
            str(self._data_source),
        )
        extracts: Sequence[ExtractMetadata]
        extracts = an_input.fetch_data_source_extracts(
            data_source_type=self._data_source_type,
            data_source=self._data_source,
        )
        data_source_extracts: Mapping[str, ExtractMetadata] = {
            _k: next(_v) for _k, _v in groupby(extracts, lambda _e: _e.id)
        }
        self._data_source.extract_metadata = data_source_extracts
        return data_source_extracts


class FetchDataSources(Consumer[Sequence[DataSourceType]]):
    """
    Fetch all the :class:`data sources <DataSource>` for the given
    :class:`data source types <DataSourceType>`.
    """

    def __init__(self, transport: Transport):
        self._transport: Transport = transport
        super().__init__(self._consume)

    def _consume(self, an_input: Sequence[DataSourceType]) -> None:
        _LOGGER.info("Fetching data sources.")
        executor: ConcurrentExecutor[
            Transport, Sequence[Mapping[str, DataSource]]
        ] = ConcurrentExecutor(
            *self._data_source_types_to_tasks(an_input), initial_value=list()
        )
        executor(self._transport)  # noqa

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


class FetchExtractMetadata(Consumer[Sequence[DataSourceType]]):
    """
    Fetch all :class:`extract metadata <ExtractMetadata>` for the given
    :class:`data sources <DataSource>`.
    """

    def __init__(self, transport: Transport):
        self._transport: Transport = transport
        super().__init__(self._consume)

    def _consume(self, an_input: Sequence[DataSourceType]) -> None:
        _LOGGER.info("Fetching extract metadata.")
        data_sources: Sequence[Tuple[DataSourceType, DataSource]] = tuple(
            chain.from_iterable(
                # Map each data_source_type to tuples of the data_source_type
                # and each of its data sources.
                map(
                    lambda _dst: product((_dst,), _dst.data_sources.values()),
                    an_input,
                )
            )
        )
        executor: ConcurrentExecutor[
            Transport, Sequence[Mapping[str, ExtractMetadata]]
        ] = ConcurrentExecutor(
            *self._data_sources_to_tasks(data_sources), initial_value=list()
        )
        executor(self._transport)  # noqa

    @staticmethod
    def _data_sources_to_tasks(
        data_sources: Iterable[Tuple[DataSourceType, DataSource]]
    ) -> Sequence[DoFetchDataSourceExtracts]:
        return tuple(
            (
                DoFetchDataSourceExtracts(
                    data_source_type=_data_source[0],
                    data_source=_data_source[1],
                )
                for _data_source in data_sources
            )
        )
