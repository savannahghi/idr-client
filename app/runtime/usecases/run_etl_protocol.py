import builtins
from collections.abc import Iterable
from concurrent.futures import Executor, ThreadPoolExecutor
from contextlib import ExitStack
from typing import Any

from attrs import define, field
from toolz import compose, juxt

from app.core import Task
from app.core_v1.domain import (
    DataSink,
    DataSinkMetadata,
    DataSource,
    DataSourceMetadata,
    ETLProtocol,
    ExtractMetadata,
    MetadataSource,
)
from app.core_v1.exceptions import TransientError
from app.lib import Retry, if_exception_type_factory
from app.runtime.constants import APP_DISPATCHER_REG_KEY
from app.runtime.utils import dispatch

from .etl_workflow import ETLWorkflow

# =============================================================================
# CONSTANTS
# =============================================================================

_if_idr_transient_exception = if_exception_type_factory(TransientError)


# =============================================================================
# HELPERS
# =============================================================================


@Retry(predicate=_if_idr_transient_exception)
def _do_provide_data_sink_meta(
    metadata_source: MetadataSource[Any, Any, Any],
) -> Iterable[DataSinkMetadata]:
    return metadata_source.provide_data_sink_meta()


@Retry(predicate=_if_idr_transient_exception)
def _do_provide_data_source_meta(
    metadata_source: MetadataSource[Any, Any, Any],
) -> Iterable[DataSourceMetadata]:
    return metadata_source.provide_data_source_meta()


@Retry(predicate=_if_idr_transient_exception)
def _do_provide_extract_meta(
    metadata_source: MetadataSource[Any, Any, Any],
    data_source_meta: DataSourceMetadata,
) -> Iterable[ExtractMetadata]:
    return metadata_source.provide_extract_meta(data_source_meta)


# =============================================================================
# USE CASES
# =============================================================================


@define(eq=False, order=False)
class RunETLProtocol(Task[None, None]):
    _etl_protocol: ETLProtocol[Any, Any, Any, Any, Any, Any] = field()

    def __attrs_post_init__(self) -> None:
        self._data_sinks: list[DataSink[Any, Any, Any]] = []
        self._data_sources: list[
            tuple[DataSource[Any, Any, Any], DataSourceMetadata]
        ] = []
        self._data_sink_metas: list[DataSinkMetadata] = []
        self._data_source_metas: list[DataSourceMetadata] = []
        self._protocol_stack: ExitStack = ExitStack()
        self._executor: Executor = ThreadPoolExecutor(
            thread_name_prefix=self._etl_protocol.id,
        )
        self._set_up_resources()

    def execute(self, an_input: None) -> None:
        import app

        app_dispatcher: dispatch.Dispatcher
        app_dispatcher = app.registry_v1.get(APP_DISPATCHER_REG_KEY)
        with self._protocol_stack:
            for metadata_source in self._etl_protocol.metadata_sources:
                self._data_sink_metas.extend(
                    _do_provide_data_sink_meta(
                        metadata_source=metadata_source,
                    ),
                )
                self._data_source_metas.extend(
                    self._do_get_data_source_and_extract_metas(
                        metadata_source=metadata_source,
                    ),
                )

            self._load_data_sources()
            self._load_data_sinks()

            self._start_etl_workflows(app_dispatcher)

    def _load_data_sinks(self) -> None:
        self._data_sinks.extend(
            builtins.map(
                compose(
                    self._protocol_stack.enter_context,
                    self._etl_protocol.data_sink_factory,
                ),
                self._data_sink_metas,
            ),
        )

    def _load_data_sources(self) -> None:
        self._data_sources.extend(
            builtins.map(
                juxt(
                    compose(
                        self._protocol_stack.enter_context,
                        self._etl_protocol.data_source_factory,
                    ),
                    lambda _s: _s,
                ),
                self._data_source_metas,
            ),
        )

    def _set_up_resources(self) -> None:
        for metadata_source in self._etl_protocol.metadata_sources:
            self._protocol_stack.enter_context(metadata_source)
        for metadata_sink in self._etl_protocol.metadata_sinks:
            self._protocol_stack.enter_context(metadata_sink)
        self._protocol_stack.enter_context(
            self._etl_protocol.upload_metadata_factory,
        )
        self._protocol_stack.enter_context(self._executor)

    def _start_etl_workflows(
        self,
        app_dispatcher: dispatch.Dispatcher,
    ) -> None:
        for data_source, data_source_meta in self._data_sources:
            for _, extract_meta in data_source_meta.extract_metadata.items():
                app_dispatcher.send(
                    dispatch.PreETLWorkflowRunSignal(
                        etl_protocol=self._etl_protocol,
                        extract_meta=extract_meta,
                    ),
                )
                ETLWorkflow(
                    data_source=data_source,  # pyright: ignore
                    extract_processor_factory=self._etl_protocol.extract_processor_factory,  # pyright: ignore  # noqa: E501
                    upload_metadata_factory=self._etl_protocol.upload_metadata_factory,  # pyright: ignore  # noqa: E501
                    metadata_sinks=self._etl_protocol.metadata_sinks,  # pyright: ignore  # noqa: E501
                    data_sinks=self._data_sinks,  # pyright: ignore
                ).execute(extract_meta)
                app_dispatcher.send(
                    dispatch.PostETLWorkflowRunSignal(
                        etl_protocol=self._etl_protocol,
                        extract_meta=extract_meta,
                    ),
                )

    @staticmethod
    def _do_get_data_source_and_extract_metas(
        metadata_source: MetadataSource[Any, Any, Any],
    ) -> Iterable[DataSourceMetadata]:
        data_source_metas = list(_do_provide_data_source_meta(metadata_source))
        for data_source_meta in data_source_metas:
            data_source_meta.extract_metadata = {
                extract_meta.id: extract_meta
                for extract_meta in _do_provide_extract_meta(
                    metadata_source=metadata_source,
                    data_source_meta=data_source_meta,
                )
            }
        return data_source_metas
