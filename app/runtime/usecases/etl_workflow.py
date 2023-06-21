from collections.abc import Callable, Iterable, Sequence
from contextlib import ExitStack
from typing import Any

from attrs import define, field

from app.core import Task
from app.core.domain import (
    CleanedData,
    DataSink,
    DataSinkStream,
    DataSource,
    DataSourceStream,
    ExtractMetadata,
    ExtractProcessor,
    MetadataSink,
    RawData,
    UploadMetadata,
    UploadMetadataFactory,
)
from app.core.exceptions import TransientError
from app.lib import Retry, if_exception_type_factory

# =============================================================================
# CONSTANTS
# =============================================================================

_if_idr_transient_exception = if_exception_type_factory(TransientError)


# =============================================================================
# HELPERS
# =============================================================================


@Retry(predicate=_if_idr_transient_exception)
def _create_new_upload_meta(
    upload_meta_factory: UploadMetadataFactory[Any, Any],
    extract_metadata: ExtractMetadata,
) -> UploadMetadata:
    return upload_meta_factory.new_upload_meta(extract_meta=extract_metadata)


@Retry(predicate=_if_idr_transient_exception)
def _do_consume(
    data_sink_stream: DataSinkStream[Any, Any],
    clean_data: CleanedData[Any],
    progress: float,
) -> None:
    data_sink_stream.consume(clean_data=clean_data, progress=progress)


@Retry(predicate=_if_idr_transient_exception)
def _do_consume_upload_meta(
    metadata_sink: MetadataSink,
    upload_meta: UploadMetadata,
) -> None:
    metadata_sink.consume_upload_meta(upload_meta=upload_meta)


@Retry(predicate=_if_idr_transient_exception)
def _do_extract(
    data_source_stream: DataSourceStream[Any, Any],
) -> tuple[RawData[Any], float]:
    return next(data_source_stream)


@Retry(predicate=_if_idr_transient_exception)
def _do_process(
    extract_processor: ExtractProcessor[Any, Any, Any],
    raw_data: RawData[Any],
    extract_metadata: ExtractMetadata,
) -> CleanedData[Any]:
    return extract_processor.process(
        raw_data=raw_data,
        extract_metadata=extract_metadata,
    )


@Retry(predicate=_if_idr_transient_exception)
def _do_start_consumption(
    data_sink: DataSink[Any, Any, Any],
    upload_meta: UploadMetadata,
) -> DataSinkStream[Any, Any]:
    return data_sink.start_consumption(upload_metadata=upload_meta)


@Retry(predicate=_if_idr_transient_exception)
def _do_start_extraction(
    data_source: DataSource[Any, Any, Any],
    extract_metadata: ExtractMetadata,
) -> DataSourceStream[Any, Any]:
    return data_source.start_extraction(extract_metadata=extract_metadata)


# =============================================================================
# ETL Workflow
# =============================================================================


@define(order=False, eq=False)
class ETLWorkflow(Task[ExtractMetadata, None]):
    """Main runtime concurrency unit."""

    _data_source: DataSource[Any, Any, Any] = field()
    _extract_processor_factory: Callable[
        [],
        ExtractProcessor[Any, Any, Any],
    ] = field()
    _upload_metadata_factory: UploadMetadataFactory[Any, Any] = field()
    _metadata_sinks: Iterable[MetadataSink[Any]] = field()
    _data_sinks: Iterable[DataSink[Any, Any, Any]] = field()

    def execute(self, an_input: ExtractMetadata) -> None:
        with ExitStack() as workflow_stack:
            draw_stream: DataSourceStream[Any, Any]
            draw_stream = workflow_stack.enter_context(
                _do_start_extraction(
                    data_source=self._data_source,
                    extract_metadata=an_input,
                ),
            )
            upload_meta: UploadMetadata = _create_new_upload_meta(
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
            self._drain_upload_metadata(upload_meta)

    def _drain_upload_metadata(self, upload_meta: UploadMetadata) -> None:
        for meta_sink in self._metadata_sinks:
            _do_consume_upload_meta(
                metadata_sink=meta_sink,
                upload_meta=upload_meta,
            )

    def _run_etl(
        self,
        draw_stream: DataSourceStream[Any, Any],
        extract_metadata: ExtractMetadata,
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
        except DataSourceStream.StopExtraction:
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
