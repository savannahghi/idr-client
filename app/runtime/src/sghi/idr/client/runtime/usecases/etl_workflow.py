import operator
from collections.abc import Callable, Iterable
from contextlib import ExitStack
from typing import Any

from attrs import define, field
from sghi.idr.client.core.domain import (
    CleanedData,
    DataProcessor,
    DataSink,
    DataSinkSelector,
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
from toolz import pipe
from toolz.curried import map

# =============================================================================
# CONSTANTS
# =============================================================================

_if_idr_transient_exception = if_exception_type_factory(TransientError)


# =============================================================================
# HELPERS
# =============================================================================


@Retry(predicate=_if_idr_transient_exception)
def _create_new_drain_meta(
    drain_meta_factory: DrainMetadataFactory[Any, Any],
    draw_meta: DrawMetadata,
) -> DrainMetadata:
    return drain_meta_factory.new_drain_meta(draw_meta=draw_meta)


@Retry(predicate=_if_idr_transient_exception)
def _do_drain(
    data_sink_stream: DataSinkStream[Any, Any],
    clean_data: CleanedData[Any],
    progress: float,
) -> None:
    data_sink_stream.drain(clean_data=clean_data, progress=progress)


@Retry(predicate=_if_idr_transient_exception)
def _do_draw(
    data_source_stream: DataSourceStream[Any, Any],
) -> tuple[RawData[Any], float]:
    return next(data_source_stream)


@Retry(predicate=_if_idr_transient_exception)
def _do_process(
    data_processor: DataProcessor[Any, Any, Any],
    raw_data: RawData[Any],
    draw_metadata: DrawMetadata,
) -> CleanedData[Any]:
    return data_processor.process(
        raw_data=raw_data,
        draw_metadata=draw_metadata,
    )


@Retry(predicate=_if_idr_transient_exception)
def _do_start_drain(
    data_sink: DataSink[Any, Any, Any],
    drain_meta: DrainMetadata,
) -> DataSinkStream[Any, Any]:
    return data_sink.start_drain(drain_metadata=drain_meta)


@Retry(predicate=_if_idr_transient_exception)
def _do_start_draw(
    data_source: DataSource[Any, Any, Any],
    draw_meta: DrawMetadata,
) -> DataSourceStream[Any, Any]:
    return data_source.start_draw(draw_metadata=draw_meta)


@Retry(predicate=_if_idr_transient_exception)
def _do_take_upload_meta(
    metadata_consumer: MetadataConsumer,
    drain_meta: DrainMetadata,
) -> None:
    metadata_consumer.take_drain_meta(drain_meta=drain_meta)


# =============================================================================
# ETL Workflow
# =============================================================================


@define(order=False, eq=False)
class ETLWorkflow(Task[DrawMetadata, None]):
    """Main runtime concurrency unit."""

    _data_source: DataSource[Any, Any, Any] = field()
    _data_processor_factory: Callable[
        [],
        DataProcessor[Any, Any, Any],
    ] = field()
    _drain_metadata_factory: DrainMetadataFactory[Any, Any] = field()
    _data_sinks: Iterable[DataSink[Any, Any, Any]] = field()
    _data_sink_selector: DataSinkSelector[Any, Any, Any, Any] = field()
    _metadata_consumer: MetadataConsumer[Any] = field()
    _drain_streams: dict[str, DataSinkStream[Any, Any]] = field(
        factory=dict, init=False,
    )

    def execute(self, an_input: DrawMetadata) -> None:
        with ExitStack() as workflow_stack:
            draw_stream: DataSourceStream[Any, Any]
            draw_stream = workflow_stack.enter_context(
                _do_start_draw(
                    data_source=self._data_source,
                    draw_meta=an_input,
                ),
            )
            drain_meta: DrainMetadata = _create_new_drain_meta(
                drain_meta_factory=self._drain_metadata_factory,
                draw_meta=an_input,
            )

            self._drain_streams.update(
                {
                    # TODO: Name is not unique. Change this to a unique key.
                    #  Consider adding DataSinkMetadata as a required property
                    #  of a DataSink. This way, the ID of the DataSinkMetadata
                    #  can be used as unique key.
                    _data_sink.name: workflow_stack.enter_context(
                        _do_start_drain(_data_sink, drain_meta),
                    )
                    for _data_sink in self._data_sinks
                },
            )
            self._run_etl(
                draw_stream=draw_stream,
                draw_metadata=an_input,
                drain_meta=drain_meta,
            )
            _do_take_upload_meta(
                metadata_consumer=self._metadata_consumer,
                drain_meta=drain_meta,
            )

    def _run_etl(
        self,
        draw_stream: DataSourceStream[Any, Any],
        draw_metadata: DrawMetadata,
        drain_meta: DrainMetadata,
    ) -> None:
        try:
            while True:
                raw_data, progress = _do_draw(draw_stream)
                with self._data_processor_factory() as data_processor:
                    clean_data: CleanedData[Any] = _do_process(
                        data_processor=data_processor,
                        raw_data=raw_data,
                        draw_metadata=draw_metadata,
                    )
                    data_sinks: Iterable[DataSink[Any, Any, Any]]
                    data_sinks = self._data_sink_selector.select(
                        data_sinks=self._data_sinks,
                        drain_meta=drain_meta,
                        clean_data=clean_data,
                    )
                    drain_streams: Iterable[DataSinkStream[Any, Any]]
                    drain_streams = pipe(
                        data_sinks,
                        # TODO: Use a unique key instead of name.
                        map(operator.attrgetter("name")),
                        map(self._drain_streams.get),
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
            _do_drain(
                data_sink_stream=drain_stream,
                clean_data=clean_data,
                progress=progress,
            )
