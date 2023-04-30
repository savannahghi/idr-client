from abc import ABCMeta, abstractmethod
from collections.abc import Iterator, Sequence
from typing import Any, Generic, Self, TypeVar, cast

from attrs import define, field
from sqlalchemy import Connection, CursorResult, Engine, Row, create_engine

from app.core_v1.domain import (
    BaseData,
    BaseDataSource,
    BaseDataSourceStream,
    RawData,
)

from .metadata import (
    BaseSQLDataSourceMetadata,
    BaseSQLExtractMetadata,
    SimpleSQLDatabaseDescriptor,
    SimpleSQLQuery,
)

# =============================================================================
# TYPES
# =============================================================================

_EM = TypeVar("_EM", bound=BaseSQLExtractMetadata)
_RD = TypeVar("_RD", bound=RawData)

_DBRows = Sequence[Row[Any]]


# =============================================================================
# BASE OPERATIONS CLASSES
# =============================================================================

@define(slots=False)
class BaseSQLDataSource(
    BaseDataSource[_EM, "SQLRawData"], Generic[_EM], metaclass=ABCMeta,
):
    """An SQL Database."""

    @property
    @abstractmethod
    def engine(self) -> Engine:
        """Return an :class:`Engine` used to connect to the data source.

        :return: an `Engine` object used to connect to the data source.
        """
        ...

    def dispose(self) -> None:
        self._is_disposed = True
        self.engine.dispose(close=True)

    @classmethod
    @abstractmethod
    def from_data_source_meta(
        cls, data_source_meta: BaseSQLDataSourceMetadata,
    ) -> Self:
        ...


@define(slots=False)
class BaseSQLDataSourceStream(
    BaseDataSourceStream[_EM, "SQLRawData"], Generic[_EM],
    metaclass=ABCMeta,
):
    @property
    def data_source(self) -> BaseSQLDataSource[_EM]:
        return cast(BaseSQLDataSource[_EM], self._data_source)


# =============================================================================
# CONCRETE OPERATIONS IMPLEMENTATIONS
# =============================================================================


@define(slots=True)
class SQLRawData(BaseData[_DBRows], RawData[_DBRows]):
    """Raw data from an SQL database."""
    ...


@define(order=False, slots=True)
class SimpleSQLDatabase(BaseSQLDataSource[SimpleSQLQuery]):

    _engine: Engine = field()

    @property
    def engine(self) -> Engine:
        return self._engine

    def start_extraction(
            self, extract_metadata: SimpleSQLQuery,
    ) -> "SimpleSQLDataSourceStream":
        return SimpleSQLDataSourceStream(
            self,
            extract_metadata,
            self._engine.connect(),
        )

    @classmethod
    def from_data_source_meta(
        cls, data_source_meta: SimpleSQLDatabaseDescriptor,
    ) -> Self:
        return cls(
            name=data_source_meta.name,  # pyright: ignore
            description=data_source_meta.description,  # pyright: ignore
            engine=create_engine(  # pyright: ignore
                data_source_meta.database_url,
                logging_name=data_source_meta.logging_name,
                isolation_level=data_source_meta.isolation_level,
            ),
        )

    @classmethod
    def of_sqlite_in_memory(
        cls,
        name: str = "SQLite in Memory",
        description: str = "An SQLite in memory database.",
    ) -> Self:
        return cls(
            name=name,  # pyright: ignore
            description=description,  # pyright: ignore
            engine=create_engine(  # pyright: ignore
                "sqlite+pysqlite:///:memory:",
                logging_name=name,
            ),
        )


@define(order=False, slots=True)
class SimpleSQLDataSourceStream(BaseSQLDataSourceStream[SimpleSQLQuery]):
    """A simple :class:`DataSourceStream` implementation. """

    _connection: Connection = field()
    _extraction_result: CursorResult[Any] | None = field(default=None, init=False)
    _partitions: Iterator[_DBRows] | None = field(default=None, init=False)

    def __attrs_post_init__(self):
        self._prepare_connection()

    def extract(self) -> tuple[SQLRawData, float]:
        if self._extraction_result is None:
            self._extraction_result = self._connection.execute(
                self.extract_metadata.select_clause,
            )
            self._partitions = self._extraction_result.partitions()

        assert self._partitions is not None
        try:
            return SQLRawData(next(self._partitions)), -1.0
        except StopIteration:
            return SQLRawData([]), 0.0

    def dispose(self) -> None:
        self._is_disposed = True
        if self._extraction_result is not None:
            self._extraction_result.close()
        self._connection.close()

    def _prepare_connection(self) -> None:
        connection_options: dict[str, Any] = {
            "logging_token": self.extract_metadata.logging_token,
        }
        if self.extract_metadata.yield_per is not None:
            connection_options["yield_per"] = self.extract_metadata.yield_per

        self._connection = self._connection.execution_options(
            **connection_options,
        )
