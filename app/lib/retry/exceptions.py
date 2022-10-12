from app.core import IDRClientException


class RetryError(IDRClientException):
    """An exception used to indicate that a retry failed."""

    def __init__(self, exp: BaseException, message="Deadline exceeded."):
        self._exp: BaseException = exp
        super().__init__(message, self._exp)
