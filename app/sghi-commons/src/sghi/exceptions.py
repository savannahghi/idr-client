class SGHIError(Exception):
    """Base exception for most exceptions raised within SGHI projects."""

    def __init__(self, message: str | None = None, *args):
        """Initialize an ``SGHIError`` with the given parameters.

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
