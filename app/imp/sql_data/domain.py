import io
from collections.abc import Mapping, Sequence
from enum import Enum
from logging import getLogger
from typing import Any, Final

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

import app
from app.core import (
    DataSource,
    DataSourceType,
    ExtractMetadata,
    Task,
    UploadChunk,
    UploadMetadata,
)
from app.lib import (
    ChunkDataFrame,
    ImproperlyConfiguredError,
    Pipeline,
    SimpleSQLSelect,
)

from .exceptions import (
    SQLDataError,
    SQLDataExtractionOperationError,
    SQLDataSourceDisposedError,
)

# =============================================================================
# CONSTANTS
# =============================================================================


_LOGGER = getLogger(__name__)

_MYSQL_CONFIG_KEY: Final[str] = "MYSQL_DB_INSTANCE"


# =============================================================================
# HELPERS
# =============================================================================


class _DataFrameChunksToUploadChunks(
    Task[Sequence[pd.DataFrame], Sequence[bytes]],
):
    def execute(self, an_input: Sequence[pd.DataFrame]) -> Sequence[bytes]:
        return tuple(
            self.data_frame_as_bytes(_data_frame) for _data_frame in an_input
        )

    @staticmethod
    def data_frame_as_bytes(data_frame: pd.DataFrame) -> bytes:
        with io.BytesIO() as stream:
            pq.write_table(
                pa.Table.from_pandas(df=data_frame),
                where=stream,
                compression="gzip",
            )
            return stream.getvalue()


# =============================================================================
# DOMAIN ITEMS DEFINITIONS
# =============================================================================


class SupportedDBVendors(Enum):
    """The database vendors that the client can extract data from."""

    MYSQL = "MySQL"
    SQLITE_MEM = "SqLite in-memory"


class SQLDataSource(DataSource[Connection]):
    """Represents an SQL database as a source of data."""

    database_name: str
    database_vendor: SupportedDBVendors

    def __init__(self, **kwargs):
        data_source_type: SQLDataSourceType = kwargs.pop("data_source_type")
        super().__init__(**kwargs)
        self._data_source_type: SQLDataSourceType = data_source_type
        self._extract_metadata: dict[str, "SQLExtractMetadata"] = {}
        self._engine: Engine | None = None

    def __enter__(self) -> "SQLDataSource":
        if self._engine is not None:
            # TODO: Consider moving this check on the "connect_to_db" method
            #  instead.
            err_msg: str = (
                'Incorrect usage of "SQLDataSource". Nesting of context '
                "managers not allowed."
            )
            raise SQLDataError(err_msg)
        self.connect_to_db()
        return self

    @property
    def data_source_type(self) -> "SQLDataSourceType":
        return self._data_source_type

    @property
    def extract_metadata(self) -> Mapping[str, "ExtractMetadata"]:
        return self._extract_metadata

    @extract_metadata.setter
    def extract_metadata(
        self,
        extract_metadata: Mapping[str, "SQLExtractMetadata"],
    ) -> None:
        self._extract_metadata = dict(**extract_metadata)

    @property
    def is_disposed(self) -> bool:
        return bool(self._engine is None)

    def connect_to_db(self) -> None:
        """Connect to a database in readiness for data extraction.

        When instances of this class are used as a context manager, there is no
        need to call this method as it is called automatically.

        :return: None.
        """
        _LOGGER.info(
            'Connecting to the "%s" %s database.',
            self.database_name,
            self.database_vendor.value,
        )
        if self.database_vendor == SupportedDBVendors.MYSQL:
            self._engine = self._load_mysql_config()
        elif self.database_vendor == SupportedDBVendors.SQLITE_MEM:
            self._engine = self._load_sqlite_in_memory_config()
        else:  # pragma: no cover
            raise SQLDataError(
                message='Unsupported db vendor "%s"'
                % self.database_vendor.value,
            )

    def dispose(self) -> None:
        _LOGGER.debug('Disposing SQL data source "%s".', str(self))
        if self._engine is not None:
            self._engine.dispose()
        self._engine = None

    def get_extract_task_args(self) -> Connection:
        self._ensure_not_disposed()
        try:
            return self._engine.connect()  # type: ignore
        except SQLAlchemyError as exp:
            error_message: str = (
                f"Error getting a connection to the database: {exp}"
            )
            _LOGGER.exception(error_message)
            raise SQLDataExtractionOperationError(error_message) from exp

    def _ensure_not_disposed(self) -> None:
        """
        Check if this data source has already been disposed and if so, raise
        an ``SQLDataSourceDisposedError`` exception.

        :return: None.
        """
        if self.is_disposed:
            raise SQLDataSourceDisposedError()

    def _load_mysql_config(self) -> Engine:
        _LOGGER.debug(
            'Loading mysql config from settings for database "%s" and vendor '
            '"%s".',
            self.database_name,
            self.database_vendor.value,
        )
        mysql_conf: Mapping[str, Any] = app.settings.get(_MYSQL_CONFIG_KEY)
        if mysql_conf is None or not isinstance(mysql_conf, dict):
            err_msg: str = 'The setting "%s" is missing or is not valid.'
            raise ImproperlyConfiguredError(message=err_msg)
        for setting in ("host", "port", "username", "password"):
            # TODO: Revisit this, confirm if username and password are a must.
            if setting not in mysql_conf:
                err_msg: str = 'The setting "{}" is missing in "{}".'.format(
                    setting,
                    _MYSQL_CONFIG_KEY,
                )
                raise ImproperlyConfiguredError(message=err_msg)
        try:
            port = int(mysql_conf["port"])
            if port < 0 or port > 65535:
                err_msg: str = "Invalid port"
                raise ValueError(err_msg)
        except ValueError:
            err_msg: str = '"%s" is not a valid port.' % mysql_conf["port"]
            raise ImproperlyConfiguredError(message=err_msg) from None

        return create_engine(
            "mysql+pymysql://%s:%s@%s:%s/%s"
            % (
                mysql_conf["username"],
                mysql_conf["password"],
                mysql_conf["host"],
                mysql_conf["port"],
                self.database_name,
            ),
        )

    def _load_sqlite_in_memory_config(self) -> Engine:
        _LOGGER.debug("Loading SqLite in memory database.")
        return create_engine("sqlite+pysqlite:///:memory:")

    @classmethod
    def of_mapping(cls, mapping: Mapping[str, Any]) -> "SQLDataSource":
        return cls(**mapping)


class SQLDataSourceType(DataSourceType):
    """This class represents SQL databases as a source type."""

    def __init__(self, **kwargs):
        kwargs["name"] = "SQL Data Source Type"
        kwargs.setdefault(
            "description",
            "Represents SQL databases as a source type.",
        )
        super().__init__(**kwargs)
        self._data_sources: dict[str, SQLDataSource] = {}

    @property
    def code(self) -> str:
        return "sql_data"

    @property
    def data_sources(self) -> Mapping[str, SQLDataSource]:
        return self._data_sources

    @data_sources.setter
    def data_sources(self, data_sources: Mapping[str, SQLDataSource]) -> None:
        self._data_sources = dict(**data_sources)

    @classmethod
    def imp_data_source_klass(cls) -> type[DataSource]:
        return SQLDataSource

    @classmethod
    def imp_extract_metadata_klass(cls) -> type[ExtractMetadata]:
        return SQLExtractMetadata

    @classmethod
    def imp_upload_chunk_klass(cls) -> type[UploadChunk]:
        return SQLUploadChunk

    @classmethod
    def imp_upload_metadata_klass(cls) -> type[UploadMetadata]:
        return SQLUploadMetadata


class SQLExtractMetadata(ExtractMetadata[Connection, Any]):
    sql_query: str
    applicable_source_versions: Sequence[str]

    def __init__(self, **kwargs):
        data_source: SQLDataSource = kwargs.pop("data_source")
        super().__init__(**kwargs)
        self._data_source: SQLDataSource = data_source
        self._upload_meta_init_kwargs: Mapping[str, Any] | None = None

    @property
    def data_source(self) -> SQLDataSource:
        return self._data_source

    def get_upload_meta_extra_init_kwargs(
        self,
    ) -> Mapping[str, Any] | None:
        """
        Return an optional mapping of extra keyword arguments to be used when
        initializing the :class:`upload metadata <UploadMetadata>` instance
        associated with this extract.

        :return: An optional mapping of extra keyword arguments to use when
            initializing the upload metadata instance associated with this
            extract.
        """
        return self._upload_meta_init_kwargs

    def to_task(self) -> SimpleSQLSelect:
        return SimpleSQLSelect(self.sql_query)


class SQLUploadChunk(UploadChunk):
    ...


class SQLUploadMetadata(UploadMetadata[pd.DataFrame]):
    def __init__(self, **kwargs):
        extract_metadata: SQLExtractMetadata = kwargs.pop("extract_metadata")
        super().__init__(**kwargs)
        self._extract_metadata: SQLExtractMetadata = extract_metadata

    @property
    def extract_metadata(self) -> SQLExtractMetadata:
        return self._extract_metadata

    def to_task(self) -> Pipeline[pd.DataFrame, Sequence[bytes]]:
        return Pipeline(ChunkDataFrame(), _DataFrameChunksToUploadChunks())

    @classmethod
    def get_content_type(cls) -> str:
        return "application/vnd.apache-parquet"
