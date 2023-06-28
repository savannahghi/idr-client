from attrs import frozen
from sghi.idr.client.runtime.constants import APP_DISPATCHER_REG_KEY
from sghi.idr.client.runtime.ui import UI
from sghi.idr.client.runtime.utils import dispatch

from .printers import print_debug, print_error, print_info, print_success


@frozen
class SimpleUI(UI):
    """Simple :class:`UI` that prints information on the console using
    `click.echo`.
    """

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

    @staticmethod
    def on_app_start(signal: dispatch.AppPreStartSignal) -> None:
        print_info("Starting ...")

    @staticmethod
    def on_app_stop(signal: dispatch.AppPreStopSignal) -> None:
        print_success("Done 😁")

    @staticmethod
    def on_config_error(signal: dispatch.ConfigErrorSignal) -> None:
        print_error(
            error_message=signal.err_message,
            exception=signal.exception,
        )

    @staticmethod
    def on_etl_protocol_start(
        signal: dispatch.PreETLProtocolRunSignal,
    ) -> None:
        print_info(
            'Running "{}:{}" protocol ...'.format(
                signal.etl_protocol.id,
                signal.etl_protocol.name,
            ),
        )

    @staticmethod
    def on_etl_protocol_stop(
        signal: dispatch.PostETLProtocolRunSignal,
    ) -> None:
        print_info("Protocol run successfully ✔️")

    @staticmethod
    def on_runtime_error(signal: dispatch.UnhandledRuntimeErrorSignal) -> None:
        print_error(
            error_message=signal.err_message,
            exception=signal.exception,
        )

    @staticmethod
    def on_etl_workflow_start(
        signal: dispatch.PreETLWorkflowRunSignal,
    ) -> None:
        print_debug(
            "- Running ETLWorkflow for extract '{}'".format(
                signal.extract_meta.name,
            ),
            nl=False,
        )

    @staticmethod
    def on_etl_workflow_stop(
        signal: dispatch.PostETLWorkflowRunSignal,
    ) -> None:
        print_debug(" ✔️")
