from collections.abc import Sequence

from requests.exceptions import (
    ConnectionError,
    RequestException,
    Timeout,
    TooManyRedirects,
)
from requests.models import Response

from ..exceptions import HTTPTransportError, HTTPTransportTransientError
from ..typings import ResponsePredicate

# =============================================================================
# CONSTANTS
# =============================================================================

KNOWN_REQUESTS_TRANSIENT_BASE_ERRORS: Sequence[type[BaseException]] = (
    ConnectionError,
    RequestException,
    Timeout,
    TooManyRedirects,
)


# =============================================================================
# UTILITIES
# =============================================================================


def if_response_has_status_factory(
    *http_status: int,
) -> ResponsePredicate:
    """Create a response predicate for responses with the given statuses.

    :param http_status: HTTP status codes that responses of interest should
        have.

    :return: A callable that returns ``True`` for all HTTP responses that have
        the given status codes and ``False`` otherwise.
    """
    _r: Response
    return lambda _r: _r.status_code in tuple(http_status)


def if_request_accepted(response: Response) -> bool:
    """Pick any HTTP response with a status code from 100 to 308.

    These are status codes that are typically returned when the request was
    received and accepted by the server.

    :param response: The HTTP response to check.

    :return: ``True`` if the HTTP response has status code of between 100 and
        308.
    """
    return if_response_has_status_factory(
        100,
        101,
        102,
        103,
        200,
        201,
        202,
        204,
        205,
        206,
        207,
        208,
        226,
        300,
        301,
        302,
        303,
        304,
        305,
        306,
        307,
        308,
    )(response)


def to_appropriate_domain_error(
    exp: BaseException,
    message: str | None = None,
    known_transient_errors: tuple[type[BaseException]] = KNOWN_REQUESTS_TRANSIENT_BASE_ERRORS,  # noqa: E501
) -> HTTPTransportError:
    """Map an exception to the appropriate domain error.

    Given an exception, either map the error to an
    :exp:`HTTPTransportTransientError` if the error is retryable, or else
    map it to a :exp:`HTTPTransportError`.

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
        return HTTPTransportTransientError(message=message)
    return HTTPTransportError(message=message)
