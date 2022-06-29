from enum import Enum
from typing import Any, Sequence

from sqlalchemy.engine import Connection

from app.core import DataSource, ExtractMetadata, ToTask
from app.lib import SQLTask


class SupportedDBVendors(Enum):
    MYSQL = "MySQL"
    POSTGRES_SQL = "Postgres SQL"


class SQLDataSource(DataSource):
    database_name: str
    database_vendor: SupportedDBVendors


class SQLExtractMetadata(
    ExtractMetadata[SQLDataSource], ToTask[Connection, Any]
):
    sql_query: str
    applicable_source_versions: Sequence[str]

    def to_task(self) -> SQLTask[Any]:
        # TODO: Add a proper implementation here.
        return SQLTask(self.sql_query, mapper=lambda _x: _x)
