from attrs import field, frozen
from rich.console import Console
from rich.live import Live
from sghi.idr.client.runtime.constants import APP_DISPATCHER_REG_KEY
from sghi.idr.client.runtime.ui import UI
from sghi.idr.client.runtime.utils import dispatch

from .console import CONSOLE
from .protocol_ui import ETLProtocolUI, ProtocolRunStatus


def _app_live_display_factory(console: Console = CONSOLE) -> Live:
    return Live(console=console, refresh_per_second=12.5)


@frozen
class RichUI(UI):
    """:class:`UI` implementation that uses a :class:`rich.console.Console`
    to render output on the console.
    """

    _console: Console = field(default=CONSOLE, init=False)
    _etl_proto_uis: dict[str, ETLProtocolUI] = field(factory=dict, init=False)
    _live_display: Live = field(factory=_app_live_display_factory, init=False)

    def start(self) -> None:
        import sghi.idr.client.core as app

        app_dispatcher: dispatch.Dispatcher
        app_dispatcher = app.registry.get(APP_DISPATCHER_REG_KEY)
        app_dispatcher.connect(dispatch.AppPreStartSignal, self.on_app_start)
        app_dispatcher.connect(dispatch.AppPreStopSignal, self.on_app_stop)
        app_dispatcher.connect(
            dispatch.ConfigErrorSignal,
            self.on_config_error,
        )
        app_dispatcher.connect(
            dispatch.ETLWorkflowRunErrorSignal,
            self.on_etl_workflow_error,
        )
        app_dispatcher.connect(dispatch.PostConfigSignal, self.on_config_stop)
        app_dispatcher.connect(dispatch.PreConfigSignal, self.on_config_start)
        app_dispatcher.connect(
            dispatch.PostETLProtocolRunSignal,
            self.on_etl_protocol_stop,
        )
        app_dispatcher.connect(
            dispatch.PostETLWorkflowRunSignal,
            self.on_etl_workflow_stop,
        )
        app_dispatcher.connect(
            dispatch.PreETLProtocolRunSignal,
            self.on_etl_protocol_start,
        )
        app_dispatcher.connect(
            dispatch.PreETLWorkflowRunSignal,
            self.on_etl_workflow_start,
        )
        app_dispatcher.connect(
            dispatch.UnhandledRuntimeErrorSignal,
            self.on_runtime_error,
        )

    def on_app_start(self, signal: dispatch.AppPreStartSignal) -> None:
        self._console.log("[bold cyan]Starting ... ")
        self._live_display.start()

    def on_app_stop(self, signal: dispatch.AppPreStopSignal) -> None:
        self._live_display.stop()
        self._console.log("[bold green]Done :+1:")

    def on_config_error(self, signal: dispatch.ConfigErrorSignal) -> None:
        ...

    def on_config_start(self, signal: dispatch.PreConfigSignal) -> None:
        self._console.rule("[bold red]IDR Client", style="bold cyan")

    def on_config_stop(self, signal: dispatch.PostConfigSignal) -> None:
        ...

    def on_etl_protocol_start(
        self,
        signal: dispatch.PreETLProtocolRunSignal,
    ) -> None:
        status_msg: str = "Running '{}' protocol ...".format(
            signal.etl_protocol.name,
        )
        status_msg.upper()

        self._etl_proto_uis[signal.etl_protocol.id] = ETLProtocolUI(
            etl_protocol=signal.etl_protocol,  # pyright: ignore
            console=self._console,  # pyright: ignore
            status=ProtocolRunStatus.RUNNING,  # pyright: ignore
        )
        self._live_display.update(self._etl_proto_uis[signal.etl_protocol.id])

    def on_etl_protocol_stop(
        self,
        signal: dispatch.PostETLProtocolRunSignal,
    ) -> None:
        self._etl_proto_uis[signal.etl_protocol.id].complete()
        self._live_display.update(self._etl_proto_uis[signal.etl_protocol.id])

    def on_etl_workflow_error(
        self,
        signal: dispatch.ETLWorkflowRunErrorSignal,
    ) -> None:
        self._etl_proto_uis[signal.etl_protocol.id].fail_workflow(
            extract_meta=signal.extract_meta,
        )

    def on_etl_workflow_start(
        self,
        signal: dispatch.PreETLWorkflowRunSignal,
    ) -> None:
        self._etl_proto_uis[signal.etl_protocol.id].start_workflow(
            extract_meta=signal.extract_meta,
        )

    def on_etl_workflow_stop(
        self,
        signal: dispatch.PostETLWorkflowRunSignal,
    ) -> None:
        self._etl_proto_uis[signal.etl_protocol.id].stop_workflow(
            extract_meta=signal.extract_meta,
        )

    def on_runtime_error(
        self,
        signal: dispatch.UnhandledRuntimeErrorSignal,
    ) -> None:
        self._live_display.stop()
