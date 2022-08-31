from abc import ABCMeta
from typing import Generic, TypeVar

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

from app.core.task import Task

from ..retry import Retry

# =============================================================================
# TYPES
# =============================================================================

_R = TypeVar("_R")  # Result


# =============================================================================
# TASKS
# =============================================================================


class SQLTask(Generic[_R], Task[Connection, _R], metaclass=ABCMeta):
    """Base class for all SQL Tasks."""

    ...


class SimpleSQLSelect(SQLTask[pd.DataFrame]):
    """
    A task that fetches data from a database and returns the result as a pandas
    ``DataFrame``.
    """

    def __init__(self, sql_query: str):
        self._sql_query: str = sql_query

    def execute(self, connection: Connection) -> pd.DataFrame:
        # FIXME: By making this method retryable on any SQLAlchemyError, a bug
        #  is introduced. This is because whenever the first exception occurs,
        #  the connection will be automatically closed and all other retries
        #  will fail on due to be run on a closed connection.
        #  Think of a better solution for this.
        with connection:
            result: pd.DataFrame
            result = self._do_execute(connection)
        return result

    @Retry(predicate=lambda _e: isinstance(_e, SQLAlchemyError))
    def _do_execute(self, connection) -> pd.DataFrame:
        result: pd.DataFrame
        result = pd.read_sql(sql=text(self._sql_query), con=connection)
        return result
