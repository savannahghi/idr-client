from app.core import (
    DataSourceDisposedError,
    ExtractionOperationError,
    IDRClientException,
)


class SQLDataError(IDRClientException):
    """
    An exception indicating that an error occurred while working with SQL data.
    """


class SQLDataExtractionOperationError(SQLDataError, ExtractionOperationError):
    """
    An exception indicating that an error occurred while extracting data from
    an ``SQLDataSource``.
    """


class SQLDataSourceDisposedError(
    SQLDataExtractionOperationError, DataSourceDisposedError
):
    """
    An exception indicating that a forbidden operation was attempted on a
    disposed ``SQLDataSource`` instance.
    """
