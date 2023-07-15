from collections.abc import Sequence

from sqlalchemy.exc import (
    DisconnectionError,
    InvalidRequestError,
    OperationalError,
    TimeoutError,
)

from ..exceptions import SQLError, SQLTransientError

# =============================================================================
# CONSTANTS
# =============================================================================

KNOWN_SQL_ALCHEMY_TRANSIENT_BASE_ERRORS: Sequence[type[BaseException]] = (
    DisconnectionError,
    InvalidRequestError,
    OperationalError,
    TimeoutError,
)


# =============================================================================
# UTILITIES
# =============================================================================

def to_appropriate_domain_error(
    exp: BaseException,
    message: str | None = None,
    known_transient_errors: tuple[type[BaseException]] = KNOWN_SQL_ALCHEMY_TRANSIENT_BASE_ERRORS,  # noqa: E501
) -> SQLError:
    """Map an exception to the appropriate domain error.

    Given an exception, either map the error to an :exp:`SQLTransientError` if
    the error is retryable, or else map it to a :exp:`SQLError`.

    :param exp: An exception to be mapped to the appropriate domain specific
        error.
    :param message: An optional error message to pass to the returned
        exception.
    :param known_transient_errors: A tuple of exception types that are safe to
        retry.

    :return: An appropriate domain specific error based on the given
        exception.
    """
    if isinstance(exp, known_transient_errors):
        return SQLTransientError(message=message)
    return SQLError(message=message)
