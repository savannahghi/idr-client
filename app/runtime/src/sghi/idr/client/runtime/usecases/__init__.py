import operator
from typing import TYPE_CHECKING

import sghi.idr.client.core as app
from importlib_metadata import EntryPoint, entry_points
from sghi.idr.client.runtime.constants import (
    ETL_PROTOCOLS_ENTRY_POINT_GROUP_NAME,
)
from toolz.curried import groupby, map, valmap
from toolz.functoolz import pipe
from toolz.itertoolz import concat, first

from .etl_workflow import ETLWorkflow
from .run_etl_protocol import RunETLProtocol

if TYPE_CHECKING:
    from collections.abc import Callable

    from sghi.idr.client.core.domain import ETLProtocol, ETLProtocolSupplier


def _execute_protocols() -> None:
    for etl_protocol in app.registry.etl_protocols.values():
        RunETLProtocol(etl_protocol).execute(None)


def _load_etl_protocols() -> None:
    # TODO: Improve this, check that invariants are upheld, etc.
    _ep: EntryPoint
    _eps: ETLProtocolSupplier
    _eps_factory: Callable[[], ETLProtocolSupplier]
    _etl_proto: ETLProtocol
    app.registry.etl_protocols = pipe(
        entry_points(group=ETL_PROTOCOLS_ENTRY_POINT_GROUP_NAME),
        map(operator.methodcaller("load")),
        map(operator.call),
        map(operator.methodcaller("get_protocols")),
        concat,
        groupby(operator.attrgetter("id")),
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
