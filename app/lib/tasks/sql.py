from abc import ABCMeta
from logging import getLogger
from typing import Generic, TypeVar

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import ExtractionOperationError
from app.core.task import Task

# =============================================================================
# TYPES
# =============================================================================

_R = TypeVar("_R")  # Result


# =============================================================================
# CONSTANTS
# =============================================================================

_LOGGER = getLogger(__name__)


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
        try:
            with connection:
                result: pd.DataFrame
                result = pd.read_sql(sql=text(self._sql_query), con=connection)
        except SQLAlchemyError as exp:
            error_message: str = f"Unable to execute SQL query: {exp}."
            _LOGGER.exception(error_message)
            raise ExtractionOperationError(message=error_message) from exp
        return result
