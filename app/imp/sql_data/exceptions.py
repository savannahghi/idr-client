from app.core import IDRClientException


class SQLDataError(IDRClientException):
    """
    An exception indicating that an error occurred while working with SQL data.
    """


class SQLDataSourceDisposedError(SQLDataError):
    """
    An exception indicating that a forbidden operation was attempted on a
    disposed ``SQLDataSource`` instance.
    """
