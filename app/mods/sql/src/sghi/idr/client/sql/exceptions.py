from sghi.idr.client.core.exceptions import IDRClientError, TransientError


class SQLError(IDRClientError):
    """An ambiguous error occurred while operating on SQL resources."""
    ...


class SQLTransientError(SQLError, TransientError):
    """A recoverable error occurred while operating on an SQL resource."""
    ...
