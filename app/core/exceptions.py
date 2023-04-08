class IDRClientException(Exception):
    """Base exception for most explicit exceptions raised by this app."""

    def __init__(self, message: str | None = None, *args):
        """Initialize an ``IDRClientException`` with the given parameters.

        :param message: An optional error message.
        :param args: args to pass to forward to the base exception.
        """
        self._message: str | None = message
        super().__init__(self._message, *args)

    @property
    def message(self) -> str | None:
        """
        Return the error message passed to this exception at initialization
        or ``None`` if one was not given.

        :return: The error message passed to this exception at initialization
            or None if one wasn't given.
        """
        return self._message


class ExtractionOperationError(IDRClientException):
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
        self, message: str | None = "Data source is disposed.", *args
    ):
        """Initialize an ``DataSourceDisposedError`` with the given parameters.

        :param message: An optional error message.
        :param args: args to pass to forward to the base exception.
        """
        super().__init__(message, *args)


class TransportError(IDRClientException):
    """
    An exception indicating that some error occurred during transport of data
    from the client to an IDR Server or vice versa.
    """


class TransportClosedError(TransportError):
    """
    An exception indicating that an erroneous usage of a closed transport was
    made.
    """

    def __init__(self, message: str | None = "Transport closed.", *args):
        """Initialize an ``TransportClosedError`` with the given parameters.

        :param message: An optional error message.
        :param args: args to pass to forward to the base exception.
        """
        super().__init__(message, *args)
