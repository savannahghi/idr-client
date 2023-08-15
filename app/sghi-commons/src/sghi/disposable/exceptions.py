from ..exceptions import SGHIError


class ResourceDisposedError(SGHIError):
    """Indicates that a :class:`Disposable` item has already been disposed."""

    def __init__(self, message: str | None = "Resource already disposed."):
        """
        Initialize a new instance of `ResourceDisposedError`.

        :param message: Optional custom error message. If not provided, a
            default message indicating that the resource is already disposed
            will be used.
        """
        super().__init__(message=message)
