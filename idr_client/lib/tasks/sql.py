from typing import Any

from idr_client.core.task import Task


class SQLTask(Task[str, object]):

    def __init__(self, sql_query: str):
        self._sql_query = sql_query

    def execute(self, connection: Any) -> object:
        # TODO: execute a query on the given connection and map the result set
        #  into some object.
        return object()
