from __future__ import annotations

from typing import Any, Generic, Self, TypeVar, cast

from sghi.idr.client.core.domain import (
    BaseDataProcessor,
    BaseDataSink,
    BaseDataSinkStream,
    CleanedData,
    DataSinkMetadata,
    DrainMetadata,
    DrawMetadata,
    RawData,
)

# =============================================================================
# TYPES
# =============================================================================

_CD = TypeVar("_CD", bound=CleanedData)
_RD = TypeVar("_RD", bound=RawData)


# =============================================================================
# OPERATION BASE CLASSES
# =============================================================================


class NoOpDataProcessor(BaseDataProcessor[Any, _RD, _CD], Generic[_RD, _CD]):
    """:class:`DataProcessor` that takes the given :class:`RawData` and
    performs no additional processing but instead returns it as is.
    """

    def dispose(self) -> None:
        self._is_disposed = True

    def process(self, raw_data: _RD, draw_metadata: DrawMetadata) -> _CD:
        return cast(_CD, raw_data)


class NullDataSink(BaseDataSink[Any, Any, Any]):
    """:class:`DataSink` that discards all data that it receives.

    This `DataSink` returns :class:`NullDataSinkStream` instances that always
    discard all the data that they receive.
    """

    def dispose(self) -> None:
        self._is_disposed = True

    def start_drain(self, drain_metadata: DrainMetadata) -> NullDataSinkStream:
        return NullDataSinkStream(
            data_sink=self,  # pyright: ignore
            drain_metadata=drain_metadata,  # pyright: ignore
        )

    @classmethod
    def of_data_sink_meta(cls, data_sink_meta: DataSinkMetadata) -> Self:
        return cls(
            name=data_sink_meta.name,  # pyright: ignore
            data_sink_meta=data_sink_meta,  # pyright: ignore
        )


class NullDataSinkStream(BaseDataSinkStream[Any, Any]):
    """:class:`DataSinkStream` that always discards all the data drained to
    it.
    """

    def drain(self, clean_data: CleanedData, progress: float) -> None:
        ...

    def dispose(self) -> None:
        self._is_disposed = True
