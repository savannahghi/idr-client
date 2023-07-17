from collections.abc import Iterable
from typing import Any

from sghi.idr.client.core.domain import (
    CleanedData,
    DataSink,
    DataSinkSelector,
    DrainMetadata,
)


class SelectAllDataSinkSelector(DataSinkSelector[Any, Any, Any, Any]):

    def select(
        self,
        data_sinks: Iterable[DataSink[Any, Any, Any]],
        drain_meta: DrainMetadata,
        clean_data: CleanedData,
    ) -> Iterable[DataSink[Any, Any, Any]]:
        return data_sinks


class SelectNoneDataSinkSelector(DataSinkSelector[Any, Any, Any, Any]):

    def select(
        self,
        data_sinks: Iterable[DataSink[Any, Any, Any]],
        drain_meta: DrainMetadata,
        clean_data: CleanedData,
    ) -> Iterable[DataSink[Any, Any, Any]]:
        return ()
