from collections.abc import Callable

from requests.models import Response

from .lib import HTTPTransport

HTTPTransportFactory = Callable[[], HTTPTransport]
"""
Return instances of :class:`HTTPTransport`.

The returned instances should be configured and ready for use.
"""

ResponsePredicate = Callable[[Response], bool]
"""
Return ``True`` if a :class:`Response` instance meets a certain criteria,
``False`` otherwise.
"""
