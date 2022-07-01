from typing import Callable, Generic, TypeVar, cast

from sqlalchemy.engine import Connection, CursorResult

from app.core.task import Task

# =============================================================================
# TYPES
# =============================================================================

_R = TypeVar("_R")  # Result
_Mapper = Callable[[CursorResult], _R]


# =============================================================================
# TASKS
# =============================================================================


class SQLTask(Generic[_R], Task[Connection, _R]):
    def __init__(self, sql_query: str, mapper: _Mapper):
        self._sql_query: str = sql_query
        self._mapper: _Mapper = mapper

    def execute(self, connection: Connection) -> _R:
        # TODO: execute a query on the given connection and map the result set
        #  into some object.
        return cast(_R, object())
