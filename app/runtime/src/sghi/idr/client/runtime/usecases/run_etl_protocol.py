import builtins
import logging
from collections.abc import Iterable, Sequence
from concurrent.futures import (
    ALL_COMPLETED,
    Executor,
    Future,
    ThreadPoolExecutor,
    wait,
)
from contextlib import ExitStack
from logging import Logger
from typing import Any

from attrs import define, field
from sghi.idr.client.core.domain import (
    DataSink,
    DataSinkMetadata,
    DataSource,
    DataSourceMetadata,
    ETLProtocol,
    ExtractMetadata,
    MetadataSupplier,
)
from sghi.idr.client.core.exceptions import TransientError
from sghi.idr.client.core.lib import Retry, if_exception_type_factory, type_fqn
from sghi.idr.client.core.task import Task
from sghi.idr.client.runtime.constants import APP_DISPATCHER_REG_KEY
from sghi.idr.client.runtime.utils import dispatch
from toolz import compose, juxt

from .etl_workflow import ETLWorkflow

# =============================================================================
# CONSTANTS
# =============================================================================

_if_idr_transient_exception = if_exception_type_factory(TransientError)


# =============================================================================
# HELPERS
# =============================================================================


@Retry(predicate=_if_idr_transient_exception)
def _do_get_data_sink_meta(
    metadata_supplier: MetadataSupplier[Any, Any, Any],
) -> Iterable[DataSinkMetadata]:
    return metadata_supplier.get_data_sink_meta()


@Retry(predicate=_if_idr_transient_exception)
def _do_get_data_source_meta(
    metadata_supplier: MetadataSupplier[Any, Any, Any],
) -> Iterable[DataSourceMetadata]:
    return metadata_supplier.get_data_source_meta()


@Retry(predicate=_if_idr_transient_exception)
def _do_get_extract_meta(
    metadata_supplier: MetadataSupplier[Any, Any, Any],
    data_source_meta: DataSourceMetadata,
) -> Iterable[ExtractMetadata]:
    return metadata_supplier.get_extract_meta(data_source_meta)


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
        self._logger: Logger = logging.getLogger(type_fqn(self.__class__))
        self._protocol_stack: ExitStack = ExitStack()
        self._executor: Executor = ThreadPoolExecutor(
            thread_name_prefix=self._etl_protocol.id,
        )
        self._set_up_resources()

    def execute(self, an_input: None) -> None:
        import sghi.idr.client.core as app

        app_dispatcher: dispatch.Dispatcher
        app_dispatcher = app.registry.get(APP_DISPATCHER_REG_KEY)
        with self._protocol_stack:
            self._data_sink_metas.extend(
                _do_get_data_sink_meta(
                    metadata_supplier=self._etl_protocol.metadata_supplier,
                ),
            )
            self._data_source_metas.extend(
                self._do_get_data_source_and_extract_metas(
                    metadata_source=self._etl_protocol.metadata_supplier,
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

    def _run_etl_workflow(
        self,
        app_dispatcher: dispatch.Dispatcher,
        data_source: DataSource[Any, Any, Any],
        extract_meta: ExtractMetadata,
    ) -> None:
        try:
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
                metadata_consumer=self._etl_protocol.metadata_consumer,  # pyright: ignore  # noqa: E501
                data_sinks=self._data_sinks,  # pyright: ignore
            ).execute(extract_meta)
            app_dispatcher.send(
                dispatch.PostETLWorkflowRunSignal(
                    etl_protocol=self._etl_protocol,
                    extract_meta=extract_meta,
                ),
            )
        except Exception as exp:
            self._logger.exception(
                "Error running ETL workflow for extract with id '%s' and "
                "name '%s'.",
                extract_meta.id,
                extract_meta.name,
            )
            app_dispatcher.send(
                dispatch.ETLWorkflowRunErrorSignal(
                    etl_protocol=self._etl_protocol,
                    extract_meta=extract_meta,
                    err_message=str(exp),
                    exception=exp,
                ),
            )
            raise

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
        self._protocol_stack.enter_context(
            self._etl_protocol.metadata_supplier,
        )
        self._protocol_stack.enter_context(
            self._etl_protocol.metadata_consumer,
        )
        self._protocol_stack.enter_context(
            self._etl_protocol.upload_metadata_factory,
        )
        self._protocol_stack.enter_context(self._executor)

    def _start_etl_workflows(
        self,
        app_dispatcher: dispatch.Dispatcher,
    ) -> None:
        for data_source, data_source_meta in self._data_sources:
            workflow_tasks: Sequence[Future[None]] = tuple(
                self._executor.submit(
                    self._run_etl_workflow,
                    app_dispatcher=app_dispatcher,
                    data_source=data_source,
                    extract_meta=extract_meta,
                )
                for extract_meta in data_source_meta.extract_metadata.values()
            )
            wait(fs=workflow_tasks, return_when=ALL_COMPLETED)

    @staticmethod
    def _do_get_data_source_and_extract_metas(
        metadata_source: MetadataSupplier[Any, Any, Any],
    ) -> Iterable[DataSourceMetadata]:
        data_source_metas = list(_do_get_data_source_meta(metadata_source))
        for data_source_meta in data_source_metas:
            data_source_meta.extract_metadata = {
                extract_meta.id: extract_meta
                for extract_meta in _do_get_extract_meta(
                    metadata_supplier=metadata_source,
                    data_source_meta=data_source_meta,
                )
            }
        return data_source_metas
