from app.core_v1.exceptions import IDRClientError, TransientError


class HTTPTransportError(IDRClientError):
    """Unknown error occurred while performing a HTTP Transport operation."""

    ...


class HTTPTransportTransientError(HTTPTransportError, TransientError):
    """
    Recoverable error occurred while performing a HTTP Transport operation.
    """

    ...


class HTTPTransportDisposedError(HTTPTransportError):
    """Erroneous usage of a disposed `HTTPTransport` was made."""

    def __init__(self, message: str | None = "Transport disposed.", *args):
        """Initialize a `HTTPTransportDisposedError`.

        :param message: An optional error message.
        :param args: Extra arguments to pass to the base exception.
        """
        super().__init__(message, *args)
