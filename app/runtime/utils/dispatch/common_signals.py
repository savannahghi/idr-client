from typing import Any

from attrs import field, frozen

from app.core_v1.domain import ETLProtocol, ExtractMetadata

from .dispatcher import Signal


@frozen
class AppPreStartSignal(Signal):
    """Signal indicating configuration of the app is about to start."""

    ...


@frozen
class AppPreStopSignal(Signal):
    """Signal indicating configuration of the app is about to stop."""

    ...


@frozen
class ConfigErrorSignal(Signal):
    """Signal indicating that a configuration error occurred."""

    err_message: str = field()
    exception: BaseException | None = field(default=None)


@frozen
class PostConfigSignal(Signal):
    """Signal indicating configuration of the app has ended."""

    ...


@frozen
class PostETLProtocolRunSignal(Signal):
    """Signal indicating an ETL Protocol run has ended."""

    etl_protocol: ETLProtocol[Any, Any, Any, Any, Any, Any] = field()


@frozen
class PostETLWorkflowRunSignal(Signal):
    """
    Signal indicating that an ETL Workflow for a given extract has completed.
    """

    etl_protocol: ETLProtocol[Any, Any, Any, Any, Any, Any] = field()
    extract_meta: ExtractMetadata


@frozen
class PreConfigSignal(Signal):
    """Signal indicating configuration of the app is about to start."""

    ...


@frozen
class PreETLProtocolRunSignal(Signal):
    """Signal indicating that an ETL Protocol run is about to start."""

    etl_protocol: ETLProtocol[Any, Any, Any, Any, Any, Any] = field()


@frozen
class PreETLWorkflowRunSignal(Signal):
    """
    Signal indicating that an ETL Workflow for a given extract is about to run.
    """

    etl_protocol: ETLProtocol[Any, Any, Any, Any, Any, Any] = field()
    extract_meta: ExtractMetadata


@frozen
class UnhandledRuntimeErrorSignal(Signal):
    """Signal indicating that an unhandled error occurred at runtime."""

    err_message: str = field()
    exception: BaseException | None = field(default=None)
