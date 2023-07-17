import builtins
import logging
from collections.abc import Iterable
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
    DrawMetadata,
    ETLProtocol,
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
def _do_get_draw_meta(
    metadata_supplier: MetadataSupplier[Any, Any, Any],
    data_source_meta: DataSourceMetadata,
) -> Iterable[DrawMetadata]:
    return metadata_supplier.get_draw_meta(data_source_meta)


def _get_draw_metas(
    metadata_supplier: MetadataSupplier[Any, Any, Any],
    data_source_metas: Iterable[DataSourceMetadata],
) -> None:
    for data_source_meta in data_source_metas:
        data_source_meta.draw_metadata = {
            draw_meta.id: draw_meta
            for draw_meta in _do_get_draw_meta(
                metadata_supplier=metadata_supplier,
                data_source_meta=data_source_meta,
            )
        }


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
            # Wrap this under a try, catch. If the execution of one ETL
            # protocol fails, it should not prevent the rest from executing.
            try:
                app_dispatcher.send(
                    dispatch.PreETLProtocolRunSignal(
                        etl_protocol=self._etl_protocol,
                    ),
                )
                self._data_sink_metas.extend(
                    _do_get_data_sink_meta(
                        metadata_supplier=self._etl_protocol.metadata_supplier,
                    ),
                )
                self._data_source_metas.extend(
                    _do_get_data_source_meta(
                        metadata_supplier=self._etl_protocol.metadata_supplier,
                    ),
                )
                _get_draw_metas(
                    metadata_supplier=self._etl_protocol.metadata_supplier,
                    data_source_metas=self._data_source_metas,
                )

                self._load_data_sources()
                self._load_data_sinks()
                self._start_etl_workflows(app_dispatcher)
                app_dispatcher.send(
                    dispatch.PostETLProtocolRunSignal(
                        etl_protocol=self._etl_protocol,
                    ),
                )
            except Exception as exp:
                _err_msg: str = (
                    "Error running ETL protocol with id '{}' and name '{}'."
                    .format(self._etl_protocol.id, self._etl_protocol.name)
                )
                self._logger.exception(_err_msg)
                app_dispatcher.send(
                    dispatch.ETLProtocolRunErrorSignal(
                        etl_protocol=self._etl_protocol,
                        err_message=_err_msg,
                        exception=exp,
                    ),
                )

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

    def _run_etl_workflow(
        self,
        app_dispatcher: dispatch.Dispatcher,
        data_source: DataSource[Any, Any, Any],
        draw_meta: DrawMetadata,
    ) -> None:
        try:
            app_dispatcher.send(
                dispatch.PreETLWorkflowRunSignal(
                    etl_protocol=self._etl_protocol,
                    draw_meta=draw_meta,
                ),
            )
            ETLWorkflow(
                data_source=data_source,  # pyright: ignore
                data_processor_factory=self._etl_protocol.data_processor_factory,  # pyright: ignore  # noqa: E501
                drain_metadata_factory=self._etl_protocol.drain_metadata_factory,  # pyright: ignore  # noqa: E501
                data_sink_selector=self._etl_protocol.data_sink_selector,  # pyright: ignore  # noqa: E501
                data_sinks=self._data_sinks,  # pyright: ignore
                metadata_consumer=self._etl_protocol.metadata_consumer,  # pyright: ignore  # noqa: E501
            ).execute(draw_meta)
            app_dispatcher.send(
                dispatch.PostETLWorkflowRunSignal(
                    etl_protocol=self._etl_protocol,
                    draw_meta=draw_meta,
                ),
            )
        except Exception as exp:
            _err_msg: str = (
                "Error running ETL workflow for draw metadata with id '{}' "
                "and name '{}'.".format(draw_meta.id, draw_meta.name)
            )
            self._logger.exception(_err_msg)
            app_dispatcher.send(
                dispatch.ETLWorkflowRunErrorSignal(
                    etl_protocol=self._etl_protocol,
                    draw_meta=draw_meta,
                    err_message=str(exp),
                    exception=exp,
                ),
            )
            # It safe to reraise the error since this will only cause the
            # thread running this workflow to fail and not the rest.
            raise

    def _set_up_resources(self) -> None:
        self._protocol_stack.enter_context(
            self._etl_protocol.metadata_supplier,
        )
        self._protocol_stack.enter_context(
            self._etl_protocol.metadata_consumer,
        )
        self._protocol_stack.enter_context(
            self._etl_protocol.drain_metadata_factory,
        )
        self._protocol_stack.enter_context(self._executor)

    def _start_etl_workflows(
        self,
        app_dispatcher: dispatch.Dispatcher,
    ) -> None:
        # Schedule all workflows for execution on separate threads.
        workflow_tasks: list[Future[None]] = []
        for data_source, data_source_meta in self._data_sources:
            workflow_tasks.extend(
                self._executor.submit(
                    self._run_etl_workflow,
                    app_dispatcher=app_dispatcher,
                    data_source=data_source,
                    draw_meta=draw_meta,
                )
                for draw_meta in data_source_meta.draw_metadata.values()
            )

        # Wait for all workflows to complete.
        wait(fs=workflow_tasks, return_when=ALL_COMPLETED)
