from abc import ABCMeta
from typing import Generic, TypeVar

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.core.task import Task

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
        with connection:
            result: pd.DataFrame
            result = pd.read_sql(sql=text(self._sql_query), con=connection)
        return result
