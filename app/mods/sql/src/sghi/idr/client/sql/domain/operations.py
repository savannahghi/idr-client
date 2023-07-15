import logging
from abc import ABCMeta
from collections.abc import Callable, Iterator, Sequence
from logging import Logger
from typing import Any, Final, Generic, Self, TypeVar, cast

import pandas as pd
from attrs import define, field
from sghi.idr.client.core.domain import (
    BaseData,
    BaseDataSource,
    BaseDataSourceStream,
    DataSourceStream,
    RawData,
)
from sghi.idr.client.core.lib import type_fqn
from sqlalchemy import Connection, CursorResult, Engine, Row, create_engine

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

DataSourceStreamFactory = Callable[
    ["BaseSQLDataSource", _EM],
    DataSourceStream[_EM, _RD],
]


# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_MAX_EXTRACTION_ROWS: Final[int] = 50_000
"""The maximum number of rows to extract from a database at any one time."""


# =============================================================================
# HELPERS
# =============================================================================


def pd_data_frame_data_source_stream_factory(
    sql_data_source: "BaseSQLDataSource[Any, SimpleSQLQuery, PDDataFrame]",
    extract_metadata: SimpleSQLQuery,
) -> "PDDataFrameDataSourceStream":
    # TODO: Add a check to ensure that the `sql_data_source` given is not
    #  disposed.
    return PDDataFrameDataSourceStream(
        sql_data_source,
        extract_metadata,
        sql_data_source.engine.connect(),
    )


def simple_data_source_stream_factory(
    sql_data_source: "BaseSQLDataSource[Any, SimpleSQLQuery, SQLRawData]",
    extract_metadata: SimpleSQLQuery,
) -> "SimpleSQLDataSourceStream":
    # TODO: Add a check to ensure that the `sql_data_source` given is not
    #  disposed.
    return SimpleSQLDataSourceStream(
        sql_data_source,
        extract_metadata,
        sql_data_source.engine.connect(),
    )


# =============================================================================
# BASE OPERATIONS CLASSES
# =============================================================================


@define(slots=False)
class BaseSQLDataSource(
    BaseDataSource[_DM, _EM, _RD],
    Generic[_DM, _EM, _RD],
    metaclass=ABCMeta,
):
    """An SQL Database."""

    _data_source_stream_factory: Callable[
        ["BaseSQLDataSource[Any, _EM, _RD]", _EM],
        DataSourceStream[_EM, _RD],
    ] = field(
        default=simple_data_source_stream_factory,
        kw_only=True,
    )
    _engine: Engine = field()

    def __attrs_post_init__(self) -> None:
        self._logger: Logger = logging.getLogger(type_fqn(self.__class__))

    @property
    def data_source_stream_factory(
        self,
    ) -> Callable[
        ["BaseSQLDataSource[Any, _EM, _RD]", _EM],
        DataSourceStream[_EM, _RD],
    ]:
        """Return a function that will be used to supply
        :class:`DataSourceStream` instances used during extraction/draw
        operations from this data source.

        :return: A function used by this data source to supply
            `DataSourceStream` instances used during extraction/draw
            operations.
        """
        return self._data_source_stream_factory

    @property
    def engine(self) -> Engine:
        """Return an :class:`Engine` used to connect to the data source.

        :return: An `Engine` object used to connect to the data source.
        """
        return self._engine

    def dispose(self) -> None:
        self._is_disposed = True
        self.engine.dispose(close=True)
        self._logger.debug("Disposal complete.")

    def start_draw(self, draw_metadata: _EM) -> DataSourceStream[_EM, _RD]:
        self._logger.info('Start draw for metadata "%s".', draw_metadata)
        return self.data_source_stream_factory(self, draw_metadata)


@define(slots=False)
class BaseSQLDataSourceStream(
    BaseDataSourceStream[_EM, _RD],
    Generic[_EM, _RD],
    metaclass=ABCMeta,
):
    _index: int = field(default=-1, init=False)

    @property
    def data_source(self) -> BaseSQLDataSource[Any, _EM, _RD]:
        return cast(BaseSQLDataSource[Any, _EM, _RD], self._data_source)


# =============================================================================
# CONCRETE OPERATIONS IMPLEMENTATIONS
# =============================================================================


@define(slots=True)
class PDDataFrame(BaseData[pd.DataFrame], RawData[pd.DataFrame]):
    """Raw data from an SQL database as a :class:`pd.DataFrame`."""

    @property
    def content_type(self) -> str:
        return "application/octet-stream"


@define(slots=True)
class SQLRawData(BaseData[_DBRows], RawData[_DBRows]):
    """Raw data from an SQL database as :class:`sqlalchemy.Row` objects."""

    @property
    def content_type(self) -> str:
        return "application/octet-stream"


@define(order=False, slots=True)
class SimpleSQLDatabase(
    BaseSQLDataSource[SimpleSQLDatabaseDescriptor, SimpleSQLQuery, _RD],
    Generic[_RD],
):
    """Simple implementation of an SQL database as a
    :class:`~app.core.domain.DataSource`.
    """

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
            data_source_stream_factory=data_source_meta.data_source_stream_factory,  # pyright: ignore  # noqa
        )

    @classmethod
    def of_sqlite_in_memory(
        cls,
        name: str = "SQLite in Memory",
        description: str = "An SQLite in memory database.",
        isolation_level: ReadIsolationLevels = "SERIALIZABLE",
        data_source_stream_factory: Callable[
            ["SimpleSQLDatabase[Any]", SimpleSQLQuery],
            DataSourceStream[SimpleSQLQuery, Any],
        ] = simple_data_source_stream_factory,
    ) -> Self:
        return cls(
            name=name,  # pyright: ignore
            description=description,  # pyright: ignore
            engine=create_engine(  # pyright: ignore
                "sqlite+pysqlite:///:memory:",
                logging_name=name,
                isolation_level=isolation_level,
            ),
            data_source_stream_factory=data_source_stream_factory,  # pyright: ignore  # noqa
        )


@define(order=False, slots=True)
class PDDataFrameDataSourceStream(
    BaseSQLDataSourceStream[SimpleSQLQuery, PDDataFrame],
):
    """:class:`DataSourceStream` implementation that operates on SQL databases
    and returns the extracted data as a :class:`pd.DataFrame`.

    This implementation streams data from the database and thus operates as an
    unbound stream. As such, it doesn't provide any meaningful value for
    progress and always returns `-1`.
    """

    _connection: Connection = field()

    def __attrs_post_init__(self):
        self._logger: Logger = logging.getLogger(type_fqn(self.__class__))
        self._logger.debug("Prepare connection.")
        self._connection: Connection = self._connection.execution_options(
            logging_token=self._draw_metadata.logging_token,
            max_row_buffer=DEFAULT_MAX_EXTRACTION_ROWS,
            stream_results=True,
            yield_per=(
                self._draw_metadata.yield_per or DEFAULT_MAX_EXTRACTION_ROWS
            ),
        )
        self._logger.debug("Query database.")
        self._extraction_results: Iterator[pd.DataFrame] = pd.read_sql(
            sql=self._draw_metadata.select_clause,
            con=self._connection,
            chunksize=(
                self._draw_metadata.yield_per or DEFAULT_MAX_EXTRACTION_ROWS
            ),
            dtype_backend="pyarrow",
        )

    def draw(self) -> tuple[PDDataFrame, float]:
        self._logger.info(
            'Draw data - [DrawMeta="%s", Progress="Indeterminate"].',
            self.draw_metadata.name,
        )
        try:
            data: pd.DataFrame = next(self._extraction_results)
            self._index += 1
            # noinspection PyArgumentList
            return PDDataFrame(data, self._index), -1.0
        except StopIteration:
            self._logger.debug(
                'All rows for draw meta "%s" fetched, stream exhausted. '
                "Stop draw.",
                self.draw_metadata.name,
            )
            raise DataSourceStream.StopDraw from None

    def dispose(self) -> None:
        self._is_disposed = True
        self._connection.close()
        self._logger.debug("Disposal complete.")


@define(order=False, slots=True)
class SimpleSQLDataSourceStream(
    BaseSQLDataSourceStream[SimpleSQLQuery, SQLRawData],
):
    """:class:`DataSourceStream` implementation that operates on SQL databases
    and returns the extracted data as a sequence of :class:`sqlalchemy.Row`
    objects.

    This implementation streams data from the database and thus operates as an
    unbound stream. As such, it doesn't provide any meaningful value for
    progress and always returns `-1`.
    """

    _connection: Connection = field()

    def __attrs_post_init__(self) -> None:
        self._logger: Logger = logging.getLogger(type_fqn(self.__class__))
        self._logger.debug("Prepare connection.")
        self._connection: Connection = self._connection.execution_options(
            logging_token=self._draw_metadata.logging_token,
            max_row_buffer=DEFAULT_MAX_EXTRACTION_ROWS,
            stream_results=True,
            yield_per=(
                self._draw_metadata.yield_per or DEFAULT_MAX_EXTRACTION_ROWS
            ),
        )
        self._logger.debug("Query database.")
        self._extraction_result: CursorResult[Any] = self._connection.execute(
            self.draw_metadata.select_clause,
        )
        self._partitions: Iterator[_DBRows]
        self._partitions = self._extraction_result.partitions(
            self._draw_metadata.yield_per or DEFAULT_MAX_EXTRACTION_ROWS,
        )

    def draw(self) -> tuple[SQLRawData, float]:
        self._logger.info(
            'Draw data - [ExtractMeta="%s", Progress="Indeterminate"].',
            self.draw_metadata.name,
        )
        try:
            data: _DBRows = next(self._partitions)
            self._index += 1
            # noinspection PyArgumentList
            return SQLRawData(data, self._index), -1.0
        except StopIteration:
            self._logger.debug(
                'All rows for draw meta "%s" fetched, stream exhausted. '
                "Stop draw.",
                self.draw_metadata.name,
            )
            raise DataSourceStream.StopDraw from None

    def dispose(self) -> None:
        self._is_disposed = True
        self._extraction_result.close()
        self._connection.close()
        self._logger.debug("Disposal complete.")
