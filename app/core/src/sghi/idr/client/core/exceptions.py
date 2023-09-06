from sghi.exceptions import SGHIError


class IDRClientError(SGHIError):
    """Base exception for most explicit exceptions raised by the client."""


class ExtractionOperationError(IDRClientError):
    """
    An exception indicating that some error occurred during data extraction
    from a ``DataSource`` or while attempting to perform operations on/against
    a ``DataSource``.
    """


class DataSourceDisposedError(ExtractionOperationError):
    """
    An exception indicating that an erroneous usage of a disposed
    ``DataSource`` was made.
    """

    def __init__(
        self,
        message: str | None = "Data source is disposed.",
        *args,
    ):
        """Initialize an ``DataSourceDisposedError`` with the given parameters.

        :param message: An optional error message.
        :param args: args to pass to forward to the base exception.
        """
        super().__init__(message, *args)


class TransientError(IDRClientError):
    """A recoverable error occurred.

    Operations that raise these types of errors are good candidates to be
    retried using the :class:`app.lib.Retry` decorator.
    """
