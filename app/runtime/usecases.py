import builtins
from collections.abc import Iterable
from typing import Any

import click
from attrs import define, field
from toolz import juxt

import app
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

from .etl_workflow import ETLWorkflow

_if_idr_transient_exception = if_exception_type_factory(TransientError)


@define(eq=False, order=False)
class RunETLProtocol(Task[None, None]):
    _etl_protocol: ETLProtocol[Any, Any, Any, Any, Any, Any] = field()

    def __attrs_post_init__(self) -> None:
        self._data_sinks: list[DataSink] = []
        self._data_sources: list[tuple[DataSource, DataSourceMetadata]] = []
        self._data_sink_metas: list[DataSinkMetadata] = []
        self._data_source_metas: list[DataSourceMetadata] = []

    def execute(self, an_input: None) -> None:
        for metadata_source in self._etl_protocol.metadata_sources:
            self._data_sink_metas.extend(
                self._do_get_data_sink_metas(metadata_source=metadata_source),
            )
            self._data_source_metas.extend(
                self._do_get_data_source_and_extract_metas(
                    metadata_source=metadata_source,
                ),
            )

        self._load_data_sources()
        self._load_data_sinks()
        self._start_etl_workflows()
        self._dispose_resources()

    @Retry(predicate=_if_idr_transient_exception)
    def _do_get_data_sink_metas(
        self,
        metadata_source: MetadataSource[Any, Any, Any],
    ) -> Iterable[DataSinkMetadata]:
        return metadata_source.provide_data_sink_meta()

    @Retry(predicate=_if_idr_transient_exception)
    def _do_get_data_source_and_extract_metas(
        self,
        metadata_source: MetadataSource[Any, Any, Any],
    ) -> Iterable[DataSourceMetadata]:
        data_source_metas = list(metadata_source.provide_data_source_meta())
        for data_source_meta in data_source_metas:
            data_source_meta.extract_metadata = {
                extract_meta.id: extract_meta
                for extract_meta in self._do_get_extract_metas(
                    metadata_source=metadata_source,
                    data_source_meta=data_source_meta,
                )
            }
        return data_source_metas

    @Retry(predicate=_if_idr_transient_exception)
    def _do_get_extract_metas(
        self,
        metadata_source: MetadataSource[Any, Any, Any],
        data_source_meta: DataSourceMetadata,
    ) -> Iterable[ExtractMetadata]:
        return metadata_source.provide_extract_meta(data_source_meta)

    def _dispose_resources(self) -> None:
        for data_source, _ in self._data_sources:
            data_source.dispose()
        for data_sink in self._data_sinks:
            data_sink.dispose()
        for metadata_source in self._etl_protocol.metadata_sources:
            metadata_source.dispose()
        for metadata_sinks in self._etl_protocol.metadata_sinks:
            metadata_sinks.dispose()
        self._etl_protocol.upload_metadata_factory.dispose()

    def _load_data_sinks(self) -> None:
        self._data_sinks.extend(
            builtins.map(
                self._etl_protocol.data_sink_factory,
                self._data_sink_metas,
            ),
        )

    def _load_data_sources(self) -> None:
        self._data_sources.extend(
            builtins.map(
                juxt(self._etl_protocol.data_source_factory, lambda _s: _s),
                self._data_source_metas,
            ),
        )

    def _start_etl_workflows(self) -> None:
        for data_source, data_source_meta in self._data_sources:
            for _, extract_meta in data_source_meta.extract_metadata.items():
                ETLWorkflow(
                    data_source=data_source,
                    extract_processor_factory=self._etl_protocol.extract_processor_factory,
                    upload_metadata_factory=self._etl_protocol.upload_metadata_factory,
                    metadata_sinks=self._etl_protocol.metadata_sinks,
                    data_sinks=self._data_sinks,
                ).execute(extract_meta)


def start() -> None:
    click.echo(click.style("Starting ...", fg="blue"))
    for protocol_id, etl_protocol in app.registry_v1.etl_protocols.items():
        click.echo(
            click.style(
                'Running "{}:{}" protocol ...'.format(
                    protocol_id,
                    etl_protocol.name,
                ),
                fg="bright_blue",
            ),
        )
        RunETLProtocol(etl_protocol).execute(None)
        click.echo(
            click.style("✔️Protocol run successfully", fg="bright_blue"),
        )
