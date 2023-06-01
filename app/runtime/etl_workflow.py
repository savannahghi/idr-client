from collections.abc import Callable, Iterable, Sequence
from contextlib import ExitStack
from typing import Any

from attrs import define, field

from app.core import Task
from app.core_v1.domain import (
    CleanedData,
    DataSink,
    DataSinkStream,
    DataSource,
    ExtractMetadata,
    ExtractProcessor,
    MetadataSink,
    UploadMetadata,
    UploadMetadataFactory,
)


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
        with self._data_source.start_extraction(
            extract_metadata=an_input,
        ) as draw_stream, ExitStack() as drain_streams_stack:
            upload_meta: UploadMetadata
            upload_meta = self._upload_metadata_factory.new_upload_meta(
                extract_meta=an_input,
                content_type="application/vnd.apache-parquet",
            )

            drain_streams: Sequence[DataSinkStream[Any, Any]]
            drain_streams = [
                drain_streams_stack.enter_context(
                    _data_sink.start_consumption(upload_metadata=upload_meta),
                )
                for _data_sink in self._data_sinks
            ]
            for raw_data, progress in draw_stream:
                with self._extract_processor_factory() as extract_processor:
                    clean_data: CleanedData = extract_processor.process(
                        raw_data=raw_data,
                        extract_metadata=an_input,
                    )
                    for _drain_stream in drain_streams:
                        _drain_stream.consume(
                            clean_data=clean_data,
                            progress=progress,
                        )

            self._drain_upload_metadata(upload_meta)

    def _drain_clean_data(
        self,
        upload_meta: UploadMetadata,
        clean_data: CleanedData,
        progress: float,
    ) -> None:
        for data_sink in self._data_sinks:
            with data_sink.start_consumption(upload_meta) as drain_stream:
                drain_stream.consume(clean_data, progress)

    def _drain_upload_metadata(self, upload_meta: UploadMetadata) -> None:
        for meta_sink in self._metadata_sinks:
            meta_sink.consume_upload_meta(upload_meta)
