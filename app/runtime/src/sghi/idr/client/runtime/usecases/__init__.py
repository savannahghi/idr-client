from typing import TYPE_CHECKING

import sghi.idr.client.core as app
from importlib_metadata import EntryPoint, entry_points
from sghi.idr.client.runtime.constants import (
    APP_DISPATCHER_REG_KEY,
    ETL_PROTOCOLS_ENTRY_POINT_GROUP_NAME,
)
from sghi.idr.client.runtime.utils import dispatch
from toolz.curried import groupby, map, valmap
from toolz.functoolz import pipe
from toolz.itertoolz import concat, first

from .etl_workflow import ETLWorkflow
from .run_etl_protocol import RunETLProtocol

if TYPE_CHECKING:
    from collections.abc import Callable

    from sghi.idr.client.core.domain import ETLProtocol, ETLProtocolSupplier


def _execute_protocols() -> None:
    app_dispatcher: dispatch.Dispatcher
    app_dispatcher = app.registry.get(APP_DISPATCHER_REG_KEY)
    for etl_protocol in app.registry.etl_protocols.values():
        app_dispatcher.send(dispatch.PreETLProtocolRunSignal(etl_protocol))
        RunETLProtocol(etl_protocol).execute(None)
        app_dispatcher.send(dispatch.PostETLProtocolRunSignal(etl_protocol))


def _load_etl_protocols() -> None:
    # TODO: Improve this, check that invariants are upheld, etc.
    _ep: EntryPoint
    _eps: ETLProtocolSupplier
    _eps_factory: Callable[[], ETLProtocolSupplier]
    _etl_proto: ETLProtocol
    app.registry.etl_protocols = pipe(
        entry_points(group=ETL_PROTOCOLS_ENTRY_POINT_GROUP_NAME),
        map(lambda _ep: _ep.load()),
        map(lambda _eps_factory: _eps_factory()),
        map(lambda _eps: _eps.get_protocols()),
        concat,
        groupby(lambda _etl_proto: _etl_proto.id),
        valmap(first),
    )


def start() -> None:
    """Entry point for running all use-cases.

    Load and execute etl protocols.
    """

    _load_etl_protocols()
    _execute_protocols()


__all__ = [
    "ETLWorkflow",
    "RunETLProtocol",
    "start",
]
