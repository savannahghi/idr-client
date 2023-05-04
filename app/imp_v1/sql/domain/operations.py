from abc import ABCMeta, abstractmethod
from collections.abc import Iterator, Sequence
from typing import Any, Final, Generic, Self, TypeVar, cast

from attrs import define, field
from sqlalchemy import Connection, CursorResult, Engine, Row, create_engine

from app.core_v1.domain import (
    BaseData,
    BaseDataSource,
    BaseDataSourceStream,
    DataSourceStream,
    RawData,
)

from ..typings import ReadIsolationLevels
from .metadata import (
    BaseSQLDataSourceMetadata,
    BaseSQLExtractMetadata,
    SimpleSQLDatabaseDescriptor,
    SimpleSQLQuery,
)

# =============================================================================
# TYPES
# =============================================================================

_DM = TypeVar("_DM", bound=BaseSQLDataSourceMetadata)
_EM = TypeVar("_EM", bound=BaseSQLExtractMetadata)
_RD = TypeVar("_RD", bound=RawData)

_DBRows = Sequence[Row[Any]]


# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_MAX_EXTRACTION_ROWS: Final[int] = 10_000
"""The maximum number of rows to extract from a database at any one time."""


# =============================================================================
# BASE OPERATIONS CLASSES
# =============================================================================


@define(slots=False)
class BaseSQLDataSource(
    BaseDataSource[_DM, _EM, "SQLRawData"],
    Generic[_DM, _EM],
    metaclass=ABCMeta,
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


@define(slots=False)
class BaseSQLDataSourceStream(
    BaseDataSourceStream[_EM, "SQLRawData"],
    Generic[_EM],
    metaclass=ABCMeta,
):
    @property
    def data_source(self) -> BaseSQLDataSource[Any, _EM]:
        return cast(BaseSQLDataSource[Any, _EM], self._data_source)


# =============================================================================
# CONCRETE OPERATIONS IMPLEMENTATIONS
# =============================================================================


@define(slots=True)
class SQLRawData(BaseData[_DBRows], RawData[_DBRows]):
    """Raw data from an SQL database."""

    ...


@define(order=False, slots=True)
class SimpleSQLDatabase(
    BaseSQLDataSource[SimpleSQLDatabaseDescriptor, SimpleSQLQuery],
):
    """
    Simple implementation of an SQL database as a
    :class:`~app.core_v1.domain.DataSource`.
    """

    _engine: Engine = field()

    @property
    def engine(self) -> Engine:
        return self._engine

    def start_extraction(
        self,
        extract_metadata: SimpleSQLQuery,
    ) -> "SimpleSQLDataSourceStream":
        return SimpleSQLDataSourceStream(
            self,
            extract_metadata,
            self._engine.connect(),
        )

    @classmethod
    def from_data_source_meta(
        cls,
        data_source_meta: SimpleSQLDatabaseDescriptor,
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
        isolation_level: ReadIsolationLevels = "SERIALIZABLE",
    ) -> Self:
        return cls(
            name=name,  # pyright: ignore
            description=description,  # pyright: ignore
            engine=create_engine(  # pyright: ignore
                "sqlite+pysqlite:///:memory:",
                logging_name=name,
                isolation_level=isolation_level,
            ),
        )


@define(order=False, slots=True)
class SimpleSQLDataSourceStream(BaseSQLDataSourceStream[SimpleSQLQuery]):
    """
    Simple :class:`DataSourceStream` implementation that operates on SQL data.
    """

    _connection: Connection = field()

    def __attrs_post_init__(self) -> None:
        self._connection: Connection = self._connection.execution_options(
            logging_token=self._extract_metadata.logging_token,
            max_row_buffer=DEFAULT_MAX_EXTRACTION_ROWS,
            stream_results=True,
            yield_per=(
                self._extract_metadata.yield_per or DEFAULT_MAX_EXTRACTION_ROWS
            ),
        )
        self._extraction_result: CursorResult[Any] = self._connection.execute(
            self.extract_metadata.select_clause,
        )
        self._partitions: Iterator[_DBRows]
        self._partitions = self._extraction_result.partitions(
            self._extract_metadata.yield_per or DEFAULT_MAX_EXTRACTION_ROWS,
        )

    def extract(self) -> tuple[SQLRawData, float]:
        try:
            return SQLRawData(next(self._partitions)), -1.0
        except StopIteration:
            raise DataSourceStream.StopExtraction from None

    def dispose(self) -> None:
        self._is_disposed = True
        self._extraction_result.close()
        self._connection.close()
