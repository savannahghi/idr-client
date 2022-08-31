import datetime
import random
import time
from functools import partial
from logging import getLogger
from typing import Any, Callable, Final, Generator, Optional

import wrapt

from app.core import IDRClientException

# =============================================================================
# CONSTANT
# =============================================================================


_LOGGER = getLogger(__name__)

DEFAULT_DEADLINE: Final[float] = 60.0 * 5  # In seconds

DEFAULT_INITIAL_DELAY: Final[float] = 1.0  # In seconds

DEFAULT_MAXIMUM_DELAY: Final[float] = 60.0  # In seconds

DEFAULT_MULTIPLICATIVE_FACTOR: Final[float] = 2.0


# =============================================================================
# TYPES
# =============================================================================

Predicate = Callable[[Exception], bool]


# =============================================================================
# HELPERS
# =============================================================================


def retry_if_idr_exception(exp: Exception) -> bool:
    return isinstance(exp, IDRClientException)


class RetryError(IDRClientException):
    """An exception used to indicate that a retry failed."""

    def __init__(self, exp: Exception, message="Deadline exceeded."):
        self._exp: Exception = exp
        super().__init__(message, self._exp)


# =============================================================================
# RETRY CLASS
# =============================================================================


class Retry:
    def __init__(
        self,
        predicate: Predicate = retry_if_idr_exception,
        initial_delay: float = DEFAULT_INITIAL_DELAY,
        maximum_delay: float = DEFAULT_MAXIMUM_DELAY,
        multiplicative_factor: float = DEFAULT_MULTIPLICATIVE_FACTOR,
        deadline: Optional[float] = DEFAULT_DEADLINE,
    ):
        self._predicate: Predicate = predicate
        self._initial_delay: float = initial_delay
        self._maximum_delay: float = maximum_delay
        self._multiplicative_factor: float = multiplicative_factor
        self._deadline: Optional[float] = deadline

    @wrapt.decorator
    def __call__(
        self, wrapped: Callable[..., Any], instance: Any, args, kwargs
    ) -> Any:
        return self.do_retry(partial(wrapped, *args, **kwargs))

    def do_retry(self, wrapped: Callable[[], Any]) -> Any:  # noqa
        if self._deadline:
            deadline_time = datetime.datetime.now() + datetime.timedelta(
                seconds=self._deadline
            )
        else:
            deadline_time = None
        last_exp: Optional[Exception]

        for sleep in self.exponential_sleep_generator():
            try:
                return wrapped()
            except Exception as exp:
                if not self._predicate(exp):
                    raise
                last_exp = exp
            now = datetime.datetime.now()
            if deadline_time is not None:
                if deadline_time <= now:
                    raise RetryError(
                        message=(
                            "Deadline of {:.1f}s exceeded while retrying "
                            "target function ...".format(self._deadline)
                        ),
                        exp=last_exp,
                    ) from last_exp
                else:
                    remaining_time = (deadline_time - now).total_seconds()
                    sleep = min(remaining_time, sleep)
            _LOGGER.debug(
                "Retrying due to {}, sleeping for {:.1f}s ...".format(
                    last_exp, sleep
                )
            )
            time.sleep(sleep)

    def exponential_sleep_generator(self) -> Generator[float, None, None]:
        delay: float = self._initial_delay
        while True:
            # Introduce jitter by yielding a random delay.
            yield min(random.uniform(0.0, delay * 2.0), self._maximum_delay)
            delay *= self._multiplicative_factor
