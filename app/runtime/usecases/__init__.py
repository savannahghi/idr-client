import app

from ..utils.printers import print_info
from .etl_workflow import ETLWorkflow
from .run_etl_protocol import RunETLProtocol


def start() -> None:
    """Entry point for running all use-cases."""

    print_info("Starting ...")
    for protocol_id, etl_protocol in app.registry_v1.etl_protocols.items():
        print_info(
            'Running "{}:{}" protocol ...'.format(
                protocol_id,
                etl_protocol.name,
            ),
        )
        RunETLProtocol(etl_protocol).execute(None)
        print_info("✔️Protocol run successfully")


__all__ = [
    "ETLWorkflow",
    "RunETLProtocol",
    "start",
]
