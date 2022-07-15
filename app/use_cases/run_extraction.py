from itertools import chain, product
from typing import Any, List, Sequence, Tuple, TypeVar

from app.core import DataSource, DataSourceType, ExtractMetadata, Task
from app.lib import ConcurrentExecutor

from .types import RunExtractionResult

# =============================================================================
# TYPES
# =============================================================================


_DoExtractResult = Tuple[ExtractMetadata, Any]

_ExpandResult = Tuple[DataSourceType, DataSource]

_R = TypeVar("_R")


# =============================================================================
# TASKS
# =============================================================================


class ExtractDataSources(
    Task[Sequence[_ExpandResult], Sequence[RunExtractionResult]]
):
    def execute(
        self, an_input: Sequence[_ExpandResult]
    ) -> Sequence[RunExtractionResult]:
        # FIXME: This is a placeholder, add a proper implementation.
        results: List[RunExtractionResult] = []
        for _expand in an_input:
            data_source: DataSource = _expand[1]
            with data_source:
                executor: ConcurrentExecutor[
                    DataSource, Sequence[_DoExtractResult]
                ]
                executor = ConcurrentExecutor(
                    *map(
                        lambda _e: DoExtract(_e),
                        data_source.extract_metadata.values(),
                    ),
                    initial_value=list(),
                )
                extracts: Sequence[_DoExtractResult] = executor.execute(
                    data_source
                )
                for _extract in extracts:
                    results.append(
                        (_expand[0], _expand[1], _extract[0], _extract[1])
                    )
        return results


class DoExtract(Task[DataSource, _DoExtractResult]):
    def __init__(self, extract_metadata: ExtractMetadata):
        self._extract_metadata: ExtractMetadata = extract_metadata

    def execute(self, an_input: DataSource) -> _DoExtractResult:
        task_args: Any = an_input.get_extract_task_args()
        extract: Any = self._extract_metadata.to_task().execute(task_args)
        return self._extract_metadata, extract


class ExpandDataSourceType(
    Task[Sequence[DataSourceType], Sequence[_ExpandResult]]
):
    """
    Expand a :class:`data source type <DataSourceType>` into a sequence of its
    constituent domain objects. That is, for each data source type, return
    a sequence consisting of a tuple of:
    1. The data source type.
    2. A data source in that data source type.
    3. An extract metadata instance in that data source.

    Thus the returned sequence will contain elements equal to the total number
    of extract metadata instances in each data source.
    """

    def execute(
        self, an_input: Sequence[DataSourceType]
    ) -> Sequence[_ExpandResult]:
        return tuple(
            chain.from_iterable(
                map(
                    lambda _dst: product((_dst,), _dst.data_sources.values()),
                    an_input,
                )
            )
        )


# TODO: Add more tasks here to post process extraction results. E.g, handle
#  errors if they occurred, etc.
