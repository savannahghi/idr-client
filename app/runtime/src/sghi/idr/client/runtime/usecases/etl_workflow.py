from collections.abc import Callable, Iterable, Sequence
from contextlib import ExitStack
from typing import Any

from attrs import define, field
from sghi.idr.client.core.domain import (
    CleanedData,
    DataProcessor,
    DataSink,
    DataSinkStream,
    DataSource,
    DataSourceStream,
    DrainMetadata,
    DrainMetadataFactory,
    DrawMetadata,
    MetadataConsumer,
    RawData,
)
from sghi.idr.client.core.exceptions import TransientError
from sghi.idr.client.core.lib import Retry, if_exception_type_factory
from sghi.idr.client.core.mixins import Task

# =============================================================================
# CONSTANTS
# =============================================================================

_if_idr_transient_exception = if_exception_type_factory(TransientError)


# =============================================================================
# HELPERS
# =============================================================================


@Retry(predicate=_if_idr_transient_exception)
def _create_new_upload_meta(
    upload_meta_factory: DrainMetadataFactory[Any, Any],
    extract_metadata: DrawMetadata,
) -> DrainMetadata:
    return upload_meta_factory.new_drain_meta(draw_meta=extract_metadata)


@Retry(predicate=_if_idr_transient_exception)
def _do_consume(
    data_sink_stream: DataSinkStream[Any, Any],
    clean_data: CleanedData[Any],
    progress: float,
) -> None:
    data_sink_stream.drain(clean_data=clean_data, progress=progress)


@Retry(predicate=_if_idr_transient_exception)
def _do_extract(
    data_source_stream: DataSourceStream[Any, Any],
) -> tuple[RawData[Any], float]:
    return next(data_source_stream)


@Retry(predicate=_if_idr_transient_exception)
def _do_process(
    extract_processor: DataProcessor[Any, Any, Any],
    raw_data: RawData[Any],
    extract_metadata: DrawMetadata,
) -> CleanedData[Any]:
    return extract_processor.process(
        raw_data=raw_data,
        draw_metadata=extract_metadata,
    )


@Retry(predicate=_if_idr_transient_exception)
def _do_start_consumption(
    data_sink: DataSink[Any, Any, Any],
    upload_meta: DrainMetadata,
) -> DataSinkStream[Any, Any]:
    return data_sink.start_drain(drain_metadata=upload_meta)


@Retry(predicate=_if_idr_transient_exception)
def _do_start_extraction(
    data_source: DataSource[Any, Any, Any],
    extract_metadata: DrawMetadata,
) -> DataSourceStream[Any, Any]:
    return data_source.start_draw(draw_metadata=extract_metadata)


@Retry(predicate=_if_idr_transient_exception)
def _do_take_upload_meta(
    metadata_consumer: MetadataConsumer,
    upload_meta: DrainMetadata,
) -> None:
    metadata_consumer.take_drain_meta(drain_meta=upload_meta)


# =============================================================================
# ETL Workflow
# =============================================================================


@define(order=False, eq=False)
class ETLWorkflow(Task[DrawMetadata, None]):
    """Main runtime concurrency unit."""

    _data_source: DataSource[Any, Any, Any] = field()
    _extract_processor_factory: Callable[
        [],
        DataProcessor[Any, Any, Any],
    ] = field()
    _upload_metadata_factory: DrainMetadataFactory[Any, Any] = field()
    _metadata_consumer: MetadataConsumer[Any] = field()
    _data_sinks: Iterable[DataSink[Any, Any, Any]] = field()

    def execute(self, an_input: DrawMetadata) -> None:
        with ExitStack() as workflow_stack:
            draw_stream: DataSourceStream[Any, Any]
            draw_stream = workflow_stack.enter_context(
                _do_start_extraction(
                    data_source=self._data_source,
                    extract_metadata=an_input,
                ),
            )
            upload_meta: DrainMetadata = _create_new_upload_meta(
                upload_meta_factory=self._upload_metadata_factory,
                extract_metadata=an_input,
            )

            drain_streams: Sequence[DataSinkStream[Any, Any]]
            drain_streams = [
                workflow_stack.enter_context(
                    _do_start_consumption(_data_sink, upload_meta),
                )
                for _data_sink in self._data_sinks
            ]
            self._run_etl(
                draw_stream=draw_stream,
                extract_metadata=an_input,
                drain_streams=drain_streams,
            )
            _do_take_upload_meta(
                metadata_consumer=self._metadata_consumer,
                upload_meta=upload_meta,
            )

    def _run_etl(
        self,
        draw_stream: DataSourceStream[Any, Any],
        extract_metadata: DrawMetadata,
        drain_streams: Sequence[DataSinkStream[Any, Any]],
    ) -> None:
        try:
            while True:
                raw_data, progress = _do_extract(draw_stream)
                with self._extract_processor_factory() as extract_processor:
                    clean_data: CleanedData[Any] = _do_process(
                        extract_processor=extract_processor,
                        raw_data=raw_data,
                        extract_metadata=extract_metadata,
                    )
                    self._drain_clean_data(drain_streams, clean_data, progress)
        except DataSourceStream.StopDraw:
            return

    @staticmethod
    def _drain_clean_data(
        drain_streams: Iterable[DataSinkStream[Any, Any]],
        clean_data: CleanedData[Any],
        progress: float,
    ) -> None:
        for drain_stream in drain_streams:
            _do_consume(
                data_sink_stream=drain_stream,
                clean_data=clean_data,
                progress=progress,
            )
