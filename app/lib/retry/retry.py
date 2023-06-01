import random
import time
from collections.abc import Callable, Generator, Mapping
from datetime import datetime, timedelta
from functools import partial
from logging import Logger, getLogger
from typing import Any

import wrapt

from app.core import IDRClientException

from .constants import (
    DEFAULT_DEADLINE,
    DEFAULT_INITIAL_DELAY,
    DEFAULT_MAXIMUM_DELAY,
    DEFAULT_MULTIPLICATIVE_FACTOR,
    DEFAULT_RETRY_CONFIG,
)
from .exceptions import RetryError
from .types import Predicate, RetryConfig

# =============================================================================
# HELPERS
# =============================================================================


def _enable_retries() -> bool:
    """Enable or disable retries globally."""
    from app import settings

    return settings.get("RETRY", DEFAULT_RETRY_CONFIG).get(
        "enable_retries",
        True,
    )


def if_exception_type_factory(*exp_types: type[BaseException]) -> Predicate:
    """Create a retry predicate for the given exception types.

    :param exp_types: The exception types to check for.

    :return: A callable that takes an exception and returns ``True`` if the
        provided exception is of the given types.
    """
    _exp: BaseException
    return lambda _exp: isinstance(_exp, exp_types)


def if_idr_exception(exp: BaseException) -> bool:
    """
    Retry predicate that is only applicable if an :class:`IDRClientException`
    was raised.

    :param exp: The exception that should be checked.

    :return: ``True`` if the given exception is an ``IDRClientException``,
        ``False`` otherwise.
    """
    return if_exception_type_factory(IDRClientException)(exp)


# =============================================================================
# RETRY CLASS
# =============================================================================


class Retry:
    """
    A decorator that exponentially retries a callable or an action until a
    deadline is exceeded or until a successful call is made.

    This decorator uses a predicate function to determine when it is
    appropriate to retry a failed call. By default, all
    :class:`IDRClientException` are retried.
    """

    def __init__(
        self,
        predicate: Predicate = if_idr_exception,
        initial_delay: float | None = None,
        maximum_delay: float | None = None,
        multiplicative_factor: float | None = None,
        **kwargs: float | None,
    ):
        """Create a new ``Retry`` decorator instance with the given arguments.

        :param predicate: A callable used to determine which exceptions should
            be retried.
        :param initial_delay: The minimum amount to delay in seconds. This must
            be greater than zero.
        :param maximum_delay: The maximum amount of delay in seconds before the
            next retry. This must be greater than or equal to the
            initial delay.
        :param multiplicative_factor: The multiplier applied to the delay. This
            must be greater than zero.
        :param deadline: The maximum duration to keep retrying in seconds. The
            last delay will be shorted as necessary to ensure that the retry
            will run no later than `deadline` seconds. If ``None`` is given,
            then the retry will continue indefinitely until a successful call
            is made.
        """

        self._predicate: Predicate = predicate
        self._initial_delay: float = initial_delay  # type: ignore
        self._maximum_delay: float = maximum_delay  # type: ignore
        self._multiplicative_factor: float = multiplicative_factor  # type: ignore  # noqa
        self._deadline: float | None = None
        self._kwargs: Mapping[str, float | None] = kwargs
        self._logger: Logger = getLogger(
            f"{self.__class__.__module__}.{self.__class__.__qualname__}",
        )

    @wrapt.decorator(enabled=_enable_retries)
    def __call__(
        self,
        wrapped: Callable[..., Any],
        # Types and default values are included on the rest of the arguments to
        # quiet pyright.
        instance: Any = None,  # noqa: ANN401
        args: tuple[Any, ...] = (),
        kwargs: Mapping[str, Any] | None = None,
    ) -> Any:  # noqa: ANN401
        self.load_config()
        kwargs = kwargs or {}
        return self.do_retry(partial(wrapped, *args, **kwargs))

    def calculate_deadline_time(self) -> datetime | None:
        """Determine and return the time when the last retry should be made.

        This method is only be called once per :class:`Retry <retry>` instance.
        Return the calculated deadline time or ``None`` to indicate that the
        callable should be retried indefinitely until a successful call is
        made.

        :return: The calculated deadline time or ``None``.
        """
        deadline: float | None = self._deadline
        now: datetime = datetime.now()
        return now + timedelta(seconds=deadline) if deadline else None

    def deliberate_next_retry(
        self,
        next_delay_duration: float,
        deadline_time: datetime | None,
        last_exp: BaseException,
    ) -> float:
        """
        Make a decision on whether to perform the next retry or mark the retry
        as failed by raising a :class:`RetryError`. A retry is considered as
        failed if the set deadline has already been exceeded.

        Return the duration to delay before the next retry.

        :param next_delay_duration: The next delay duration returned by the
            exponential delay generator.
        :param deadline_time: The time when the last retry should be made. When
            not ``None``, the returned delay duration will be adjusted as
            necessary not to exceed this value.
        :param last_exp: The last exception that was raised.

        :return: The next delay duration before making the next retry. This
            will be adjusted not to exceed the given deadline time.

        :raise RetryError: If the deadline has already been exceeded.
        """
        if deadline_time is None:
            return next_delay_duration
        now: datetime = datetime.now()
        if now > deadline_time:
            raise RetryError(
                message=(
                    "Deadline of {:.1f}s exceeded while retrying target "
                    "callable ...".format(self._deadline)
                ),
                exp=last_exp,
            ) from last_exp

        remaining_time = (deadline_time - now).total_seconds()
        return min(remaining_time, next_delay_duration)

    def do_retry(self, wrapped: Callable[[], Any]) -> Any:  # noqa: ANN401
        """Implement the actual retry algorithm.

        Take a callable and retry it until a successful call or the set
        deadline is exceeded. Return the return value of the callable on a
        successful call or raise :class:`RetryError` if the set deadline is
        exceeded.

        :param wrapped: The callable to be retried. This callable should take
            no arguments.

        :return: The value returned by the callable on a successful call.

        :raise RetryError: If the set deadline is exceeded.
        """
        deadline_time: datetime | None = self.calculate_deadline_time()
        last_exp: Exception

        for sleep in self.exponential_delay_generator():  # pragma: no branch
            try:
                return wrapped()
            except Exception as exp:  # noqa: BLE001
                if not self._predicate(exp):
                    raise
                last_exp = exp

            # Decide whether to proceed with the next retry or fail.
            sleep = self.deliberate_next_retry(
                next_delay_duration=sleep,
                deadline_time=deadline_time,
                last_exp=last_exp,
            )
            self._logger.debug(
                'Retrying due to "%s", sleeping for %.2f seconds ...',
                last_exp,
                sleep,
            )
            time.sleep(sleep)

        # This should never be reached. This method should either exit by
        # returning the wrapped callable's result or by raising an exception.
        err_msg: str = "The program entered an invalid state. Exiting."  # pragma: no cover # noqa: E501
        raise AssertionError(err_msg)

    def exponential_delay_generator(self) -> Generator[float, None, None]:
        """
        Return a generator that yields successive delay intervals based on the
        exponential back-off algorithm.

        :return: An exponential delay generator.
        """
        delay: float = self._initial_delay
        while True:
            # Introduce jitter by yielding a random delay.
            yield min(
                random.uniform(0.0, delay * 2.0),  # noqa: # S311
                self._maximum_delay,
            )
            delay *= self._multiplicative_factor

    def load_config(self) -> None:
        """
        Load and configure this retry instance with the values specified in
        the application settings.

        If said values aren't available, use the default values. As well as
        loading and setting the configuration values, values are checked to
        ensure for validity. Clients of this class do not have to call this
        method directly as it is always called just before the decorated
        function or method is called.

        .. note::
            This method serves the same purpose as a traditional constructor
            but is needed here to delay the access of the application settings
            before the application has completed the setup phase which would
            result in cyclic import errors. This issue arises because this
            class is used as a decorator on functions and methods which leads
            to it being executed at module load time *(which coincidentally
            is also what the application setup phase does, load other modules
            )*.

        :return: None.

        :raise ValueError: If any of the constraints specified in the
            constructor are violated.
        """
        from app import settings

        retry_config: RetryConfig = settings.get("RETRY", DEFAULT_RETRY_CONFIG)

        self._initial_delay = (  # type: ignore
            self._initial_delay
            or retry_config.get("default_initial_delay", DEFAULT_INITIAL_DELAY)
        )
        self._maximum_delay: float = (  # type: ignore
            self._maximum_delay
            or retry_config.get("default_maximum_delay", DEFAULT_MAXIMUM_DELAY)
        )
        self._multiplicative_factor: float = (  # type: ignore
            self._multiplicative_factor
            or retry_config.get(
                "default_multiplicative_factor",
                DEFAULT_MULTIPLICATIVE_FACTOR,
            )
        )
        self._deadline: float | None = self._kwargs.get(  # type: ignore
            "deadline",
            retry_config.get("default_deadline", DEFAULT_DEADLINE),
        )

        self._check_invariants()

    def _check_invariants(self) -> None:
        """Check if the class invariants are observed."""
        from app.lib import ensure_greater_than

        ensure_greater_than(
            self._initial_delay,
            0.0,
            message="The initial_delay must be greater 0.",
        )
        ensure_greater_than(
            self._maximum_delay,
            (self._initial_delay - 1),
            message=(
                'The maximum delay ("{:.2f}") must be greater than or '
                'equal to the initial value ("{:.2f}").'.format(
                    self._maximum_delay,
                    self._initial_delay,
                )
            ),
        )
        ensure_greater_than(
            self._multiplicative_factor,
            0.0,
            "The multiplicative_factor must be than 0.",
        )
