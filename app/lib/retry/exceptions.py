from app.core import IDRClientError


class RetryError(IDRClientError):
    """An exception used to indicate that a retry failed."""

    def __init__(
        self,
        exp: BaseException,
        message: str = "Deadline exceeded.",
    ):
        self._exp: BaseException = exp
        super().__init__(message, self._exp)
