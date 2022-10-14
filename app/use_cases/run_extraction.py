from concurrent.futures import Future, as_completed
from itertools import chain, groupby
from logging import getLogger
from typing import Any, Sequence, Tuple

from app.core import (
    DataSource,
    ExtractionOperationError,
    ExtractMetadata,
    Task,
)
from app.lib import (
    ConcurrentExecutor,
    Retry,
    completed_successfully,
    if_exception_type_factory,
)

from .types import RunExtractionResult

# =============================================================================
# CONSTANTS
# =============================================================================

_LOGGER = getLogger(__name__)


# =============================================================================
# TYPES
# =============================================================================

_GroupedSiblingExtracts = Tuple[DataSource, Sequence[ExtractMetadata]]


# =============================================================================
# HELPER TASKS
# =============================================================================


class DoExtract(Task[DataSource, RunExtractionResult]):
    """
    Run an extract against a data source and return a tuple of the extract and
    the extract result.
    """

    def __init__(self, extract_metadata: ExtractMetadata):
        self._extract_metadata: ExtractMetadata = extract_metadata

    @Retry(predicate=if_exception_type_factory(ExtractionOperationError))
    def execute(self, an_input: DataSource) -> RunExtractionResult:
        # The extract should only be run against its parent data source.
        assert self._extract_metadata.data_source == an_input

        _LOGGER.info(
            'Running extraction for extract metadata="%s".',
            str(self._extract_metadata),
        )
        task_args: Any = an_input.get_extract_task_args()
        extract: Any = self._extract_metadata.to_task().execute(task_args)
        return self._extract_metadata, extract


# =============================================================================
# MAIN TASKS
# =============================================================================


class GroupSiblingExtracts(
    Task[Sequence[ExtractMetadata], Sequence[_GroupedSiblingExtracts]]
):
    """
    Group extracts owned by the same :class:`data source <DataSource>` together
    in preparation for extraction.
    """

    def execute(
        self, an_input: Sequence[ExtractMetadata]
    ) -> Sequence[_GroupedSiblingExtracts]:
        _LOGGER.debug("Grouping extracts.")
        # Sort the given extracts by their parent data source's id.
        extracts: Sequence[ExtractMetadata] = sorted(
            an_input, key=lambda _e: _e.data_source.id
        )
        # Group extracts by their parent data source. Note unlike the previous
        # statement, the key function in this statement compares data source
        # instances directly instead of comparing them by their IDs. That is
        # intentional.
        grouped_extracts: Sequence[_GroupedSiblingExtracts] = tuple(
            (_k, tuple(_v))
            for _k, _v in groupby(extracts, key=lambda _e: _e.data_source)
        )
        return grouped_extracts


class RunDataSourceExtracts(
    Task[Sequence[_GroupedSiblingExtracts], Sequence[RunExtractionResult]]
):
    """Run extracts for each data source and return the results."""

    def execute(
        self, an_input: Sequence[_GroupedSiblingExtracts]
    ) -> Sequence[RunExtractionResult]:
        _LOGGER.debug("Running extraction for all data sources.")
        return tuple(
            chain.from_iterable(
                self.run_data_source_extracts(
                    _grouped_extract[0], _grouped_extract[1]
                )
                for _grouped_extract in an_input
            )
        )

    @staticmethod
    def run_data_source_extracts(
        data_source: DataSource, extracts: Sequence[ExtractMetadata]
    ) -> Sequence[RunExtractionResult]:
        _LOGGER.info(
            'Running extraction for data source="%s"', str(data_source)
        )
        with data_source:
            executor: ConcurrentExecutor[DataSource, RunExtractionResult]
            executor = ConcurrentExecutor(
                *(DoExtract(_extract) for _extract in extracts),
            )
            with executor:
                futures: Sequence[Future[RunExtractionResult]]
                futures = executor(data_source)  # noqa
                # Focus on completed tasks and ignore the ones that failed.
                completed_futures = as_completed(futures)
            return tuple(
                map(
                    lambda _f: _f.result(),
                    filter(
                        lambda _f: completed_successfully(_f),
                        completed_futures,
                    ),
                )
            )
