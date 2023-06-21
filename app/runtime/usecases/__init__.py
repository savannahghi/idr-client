import app
from app.runtime.constants import APP_DISPATCHER_REG_KEY
from app.runtime.utils import dispatch

from .etl_workflow import ETLWorkflow
from .run_etl_protocol import RunETLProtocol


def start() -> None:
    """Entry point for running all use-cases."""

    app_dispatcher: dispatch.Dispatcher
    app_dispatcher = app.registry.get(APP_DISPATCHER_REG_KEY)
    for etl_protocol in app.registry.etl_protocols.values():
        app_dispatcher.send(dispatch.PreETLProtocolRunSignal(etl_protocol))
        RunETLProtocol(etl_protocol).execute(None)
        app_dispatcher.send(dispatch.PostETLProtocolRunSignal(etl_protocol))


__all__ = [
    "ETLWorkflow",
    "RunETLProtocol",
    "start",
]
