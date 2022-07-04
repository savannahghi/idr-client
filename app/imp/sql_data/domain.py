from enum import Enum
from typing import Any, Dict, Mapping, Sequence

from sqlalchemy.engine import Connection

from app.core import DataSource, DataSourceType, ExtractMetadata, ToTask
from app.lib import SQLTask


class SupportedDBVendors(Enum):
    MYSQL = "MySQL"
    POSTGRES_SQL = "Postgres SQL"


class SQLDataSource(DataSource):
    database_name: str
    database_vendor: SupportedDBVendors

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._extract_metadata: Dict[str, "SQLExtractMetadata"] = dict()

    @property
    def extract_metadata(self) -> Mapping[str, "ExtractMetadata"]:
        return self._extract_metadata

    @extract_metadata.setter
    def extract_metadata(
        self, extract_metadata: Mapping[str, "SQLExtractMetadata"]
    ) -> None:
        self._extract_metadata = dict(**extract_metadata)


class SQLDataSourceType(DataSourceType[SQLDataSource]):
    def __init__(self):
        super().__init__(name="SQL Data Source Type")
        self._data_sources: Dict[str, SQLDataSource] = dict()

    @property
    def code(self) -> str:
        return "sql_data"

    @property
    def data_sources(self) -> Mapping[str, SQLDataSource]:
        return self._data_sources

    @data_sources.setter
    def data_sources(self, data_sources: Mapping[str, SQLDataSource]) -> None:
        self._data_sources = dict(**data_sources)


class SQLExtractMetadata(
    ExtractMetadata[SQLDataSource], ToTask[Connection, Any]
):
    sql_query: str
    applicable_source_versions: Sequence[str]

    def to_task(self) -> SQLTask[Any]:
        # TODO: Add a proper implementation here.
        return SQLTask(self.sql_query, mapper=lambda _x: _x)
