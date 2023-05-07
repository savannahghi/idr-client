from abc import ABCMeta, abstractmethod
from collections.abc import Callable

# noinspection PyUnresolvedReferences
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define, field
from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.sql.selectable import SelectBase

from app.core_v1.domain import (
    BaseDataSourceMetadata,
    BaseExtractMetadata,
    DataSourceStream,
    RawData,
)

from ..typings import ReadIsolationLevels

if TYPE_CHECKING:  # pragma: no cover
    # noinspection PyUnresolvedReferences
    from .operations import BaseSQLDataSource


# =============================================================================
# TYPES
# =============================================================================


_EM = TypeVar("_EM", bound="BaseSQLExtractMetadata")
_RD = TypeVar("_RD", bound=RawData)

DataSourceStreamFactory = Callable[
    ["BaseSQLDataSource[Any, _EM, _RD]", _EM],
    DataSourceStream[_EM, _RD],
]

# =============================================================================
# BASE METADATA CLASSES
# =============================================================================


@define(slots=False)
class BaseSQLDataSourceMetadata(BaseDataSourceMetadata, metaclass=ABCMeta):
    """Base descriptor for :class:`SQL data sources<DataSource>`."""

    @property
    @abstractmethod
    def data_source_stream_factory(self) -> DataSourceStreamFactory:
        ...

    @property
    @abstractmethod
    def database_url(self) -> str | URL:
        """Return a :class:`URL` used to connect to the database of interest.

        :return: A URL or URL string used to connect to the database of
            interest.
        """
        ...


@define(slots=False)
class BaseSQLExtractMetadata(BaseExtractMetadata, metaclass=ABCMeta):
    """Base `ExtractMetadata` for drawing data from SQL data sources.

    Defines properties that describe a draw operation from an SQL data source.
    """

    @property
    @abstractmethod
    def select_clause(self) -> SelectBase | TextClause:
        """Return an SQL select clause used to extract data from the DB.

        :return: An SQL select clause used to extract data from the DB.
        """
        ...


# =============================================================================
# CONCRETE METADATA IMPLEMENTATIONS
# =============================================================================


@define
class SimpleSQLDatabaseDescriptor(BaseSQLDataSourceMetadata):
    """Simple SQL database descriptor."""

    _database_url: str | URL = field()
    _isolation_level: ReadIsolationLevels = field(
        default="REPEATABLE READ",
        kw_only=True,
    )
    _logging_name: str | None = field(default=None, kw_only=True)
    _data_source_stream_factory: DataSourceStreamFactory | None = field(
        default=None,
        kw_only=True,
    )

    @property
    def data_source_stream_factory(self) -> DataSourceStreamFactory:
        from .operations import pd_data_frame_data_source_stream_factory

        return (
            self._data_source_stream_factory
            or pd_data_frame_data_source_stream_factory
        )

    @property
    def database_url(self) -> str | URL:
        return self._database_url

    @property
    def isolation_level(self) -> ReadIsolationLevels:
        """Return the transaction isolation level used in the lifespan of the
        database connections used during data extraction.

        The value should be one of: `READ COMMITTED`, `READ UNCOMMITTED` or
        `REPEATABLE READ`. This will be used as the isolation level of all
        new connections to the underlying database described by this object.

        .. seealso::

            `SQLAlchemy docs <https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine.params.isolation_level>`_

        :return: The transaction isolation level used in the lifespan of the
            database connections used during data extraction.
        """
        return self._isolation_level

    @property
    def logging_name(self) -> str:
        """Return string identifier used in the logging records generated from
        operations against the described database.

        .. seealso::

            `SQLAlchemy docs <https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.create_engine.params.logging_name>`_


        :return: A string identifier used in the logging records generated from
            operations against the described database.
        """
        return self._logging_name or self.name


@define(slots=True)
class SimpleSQLQuery(BaseSQLExtractMetadata):
    """Simple :class:`ExtractMetadata` implementation for extracting data from
    SQL databases.

    """

    _raw_sql_query: str = field()
    _yield_per: int | None = field(default=None, kw_only=True)
    # TODO: Ensure that the number is a positive integer when set.
    _logging_token: str | None = field(default=None, kw_only=True)
    _isolation_level: ReadIsolationLevels | None = field(
        default=None,
        kw_only=True,
    )

    @property
    def isolation_level(self) -> ReadIsolationLevels | None:
        """Return the transaction isolation level used in the lifespan of the
        database connections used during data extraction.

        The value should be one of: `READ COMMITTED`, `READ UNCOMMITTED`,
        `REPEATABLE READ`, when not ``None``. When set to ``None``, the
        isolation level will be set by the database engine in use which is
        set by the :attr:`SimpleSQLDatabaseDescriptor.isolation_level`
        property.

        .. seealso::

            `SQLAlchemy docs <https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Connection.execution_options.params.isolation_level>`_

        :return: The transaction isolation level used in the lifespan of the
            database connections used during data extraction.
        """
        return self._isolation_level

    @property
    def logging_token(self) -> str:
        """Return a string token used in log messages by connections during
        data extraction.

        .. seealso::

            `SQLAlchemy docs <https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Connection.execution_options.params.logging_token>`_

        :return: A string token used in log messages during data extraction.
        """
        return self._logging_token or self.name

    @property
    def raw_sql_query(self) -> str:
        """Return the textual SQL statement used in the :attr:`select_clause`
        of this :class:`extract metadata<BaseSQLExtractMetadata>` instance.

        :return: The textual SQL statement used in the select clause of this
            extract metadata instance.
        """
        return self._raw_sql_query

    @property
    def yield_per(self) -> int | None:
        """Return the maximum number of rows to be extracted at any one time
        from the source database.

        A value of `None`, indicates that all the rows from the resulting
        should all be pulled from the database at once.

        .. seealso::

            `SQLAlchemy docs <https://docs.sqlalchemy.org/en/20/core/connections.html#sqlalchemy.engine.Connection.execution_options.params.yield_per>`_

        :return: The maximum number of rows to be extracted at any one time
            from the database.
        """
        return self._yield_per

    @property
    def select_clause(self) -> TextClause:
        return text(self._raw_sql_query)
