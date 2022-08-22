from typing import Optional


class IDRClientException(Exception):
    """Base exception for most explicit exceptions raised by this app."""

    def __init__(self, message: Optional[str] = None, *args):
        """Initialize an ``IDRClientException`` with the given parameters.

        :param message: An optional error message.
        :param args: args to pass to forward to the base exception.
        """
        self._message: Optional[str] = message
        super().__init__(self._message, *args)

    @property
    def message(self) -> Optional[str]:
        """
        Return the error message passed to this exception at initialization
        or ``None`` if one was not given.

        :return: The error message passed to this exception at initialization
            or None if one wasn't given.
        """
        return self._message


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

    def __init__(self, message: Optional[str] = "Transport closed.", *args):
        """Initialize an ``TransportClosedError`` with the given parameters.

        :param message: An optional error message.
        :param args: args to pass to forward to the base exception.
        """
        super().__init__(message, *args)
