from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pytest

from app.lib import (
    Config,
    Retry,
    RetryError,
    RetryInitializer,
    if_exception_type_factory,
    if_idr_exception,
)


def test_if_idr_exception() -> None:
    """
    Assert that the ``if_idr_exception`` function returns the expected value.
    """

    assert if_idr_exception(RetryError(exp=RuntimeError()))
    assert not if_idr_exception(ValueError())


def test_if_exception_type_factory_return_value() -> None:
    """
    Assert that the ``if_exception_type_factory`` function returns the
    expected value.
    """
    predicate = if_exception_type_factory(RuntimeError, ValueError)

    assert predicate(RuntimeError())
    assert predicate(ValueError())
    assert not predicate(ZeroDivisionError())


class TestRetry(TestCase):
    """Tests for the :class:`Retry` class."""

    def setUp(self) -> None:
        super().setUp()
        self._deadline: float = 10.0
        self._app_config: Config = Config(
            settings={
                "RETRY": {
                    "default_deadline": self._deadline,
                    "enable_retries": False,
                },
            },
            settings_initializers=(RetryInitializer(),),
        )
        self._patch = patch("app.settings", self._app_config)
        self._patch.start()
        self._instance: Retry = Retry()
        self._instance.load_config()

    def tearDown(self) -> None:
        super().tearDown()
        self._patch.stop()

    def test_calculate_deadline_time_return_value_with_no_deadline(
        self,
    ) -> None:
        """
        Assert the the ``calculate_deadline_time`` method returns None when
        the ``self._deadline`` property is None.
        """
        instance = Retry(deadline=None)
        instance.load_config()

        assert instance.calculate_deadline_time() is None

    def test_calculate_deadline_time_return_value_with_deadline(self) -> None:
        """
        Assert the the ``calculate_deadline_time`` method returns the expected
        value when ``self._deadline`` property is not None.
        """
        mock_now: datetime = datetime(1970, 1, 1, 0, 0, 0, 0)
        with patch("app.lib.retry.retry.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_now
            deadline_time = mock_now + timedelta(seconds=self._deadline)

            assert self._instance.calculate_deadline_time() == deadline_time

    def test_config_is_auto_loaded_when_used_as_a_decorator(self) -> None:
        """
        Assert that when a ``Retry`` instance is used as decorator, the
        instance is automatically configured and a call to the ``load_config``
        method is not necessary.
        """
        # Callable that fails initially but eventually succeeds.
        a_callable = MagicMock(side_effect=[ValueError, AttributeError, 10])
        app_config: Config = Config(
            settings={
                "RETRY": {
                    "default_deadline": 5,
                    "default_initial_delay": 1.0,
                    "default_maximum_delay": 1.0,
                    "default_multiplicative_factor": 5,
                    "enable_retries": True,
                },
            },
            settings_initializers=(RetryInitializer(),),
        )
        instance: Retry = Retry(
            predicate=if_exception_type_factory(ValueError, AttributeError),
        )
        with patch("app.settings", app_config):
            result = instance(a_callable, None, (5, 5))()

        assert instance._deadline == 5  # type: ignore
        assert instance._initial_delay == 1.0  # type: ignore
        assert instance._maximum_delay == 1.0  # type: ignore
        assert instance._multiplicative_factor == 5  # type: ignore
        assert result == 10

    def test_deliberate_next_retry_value_with_deadline_time(self) -> None:
        """
        Assert that the ``deliberate_next_retry`` method returns the next delay
        duration as given when a ``None`` deadline time  is given.
        """
        instance = self._instance
        value = instance.deliberate_next_retry(10.0, None, RuntimeError())

        assert value == 10.0

    def test_deliberate_next_retry_value_with_valid_deadline_time(
        self,
    ) -> None:
        """
        Assert that the ``deliberate_next_retry`` method returns the next delay
        duration and adjusted not to exceed the given deadline time if
        necessary.
        """
        instance = self._instance
        mock_now: datetime = datetime(1970, 1, 1, 0, 0, 0, 0)
        with patch("app.lib.retry.retry.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_now

            # When there is more than enough time before the deadline, the
            # delay should be returned as is.
            value1 = instance.deliberate_next_retry(
                10.0,
                deadline_time=mock_now + timedelta(hours=1),
                last_exp=RuntimeError(),
            )

            # When the delay exceeds the time to the deadline, it should be
            # adjusted not to exceed the deadline.
            value2 = instance.deliberate_next_retry(
                10.0,
                deadline_time=mock_now + timedelta(seconds=5),
                last_exp=RuntimeError(),
            )

            assert value1 == 10.0
            assert value2 == 5.0

    def test_deliberate_next_retry_value_past_the_deadline_time(self) -> None:
        """
        Assert that the ``deliberate_next_retry`` method raised ``RetryError``
        when called passed the deadline time.
        """
        instance = self._instance
        mock_now: datetime = datetime(1970, 1, 1, 0, 0, 0, 0)
        with patch("app.lib.retry.retry.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_now

            with pytest.raises(RetryError, match="Deadline of"):
                instance.deliberate_next_retry(
                    10.0,
                    deadline_time=mock_now - timedelta(seconds=5),
                    last_exp=RuntimeError(),
                )

    def test_do_retry_with_failing_callable_and_a_retryable_exception(
        self,
    ) -> None:
        """
        Assert that the ``do_retry`` method calls the given callable until
        a successful call or the deadline is exceeded if the callable raises
        a retryable exception. A retryable exception is one which passes the
        predicate test of the ``Retry`` instance.
        """
        # A callable that always fails.
        a_callable1 = MagicMock(side_effect=AttributeError)
        # Callable that fails initially but eventually succeeds.
        a_callable2 = MagicMock(
            side_effect=[ValueError, ValueError, AttributeError, 10],
        )

        instance: Retry = Retry(
            predicate=if_exception_type_factory(ValueError, AttributeError),
            initial_delay=1.0,
            maximum_delay=1.0,
            multiplicative_factor=5,
            deadline=5.0,
        )
        instance.load_config()

        with pytest.raises(RetryError) as exec_info:
            # This should continue until the deadline is exceeded and the
            # error is re-raised.
            instance.do_retry(a_callable1)

        assert isinstance(exec_info.value.__cause__, AttributeError)
        # This should continue until a successful call.
        assert instance.do_retry(a_callable2) == 10
        assert a_callable2.call_count == 4

    def test_do_retry_with_failing_callable_and_non_retryable_exception(
        self,
    ) -> None:
        """
        Assert that the ``do_retry`` method re-raises the original exception if
        the a callable being retried raises a non-retryable exception. A
        non-retryable exception is one which fails the predicate test of the
        ``Retry`` instance.
        """
        instance: Retry = Retry(
            predicate=if_exception_type_factory(ValueError),
        )
        instance.load_config()

        with pytest.raises(ZeroDivisionError):
            instance.do_retry(lambda: 1 / 0)

    def test_do_retry_with_successful_callable(self) -> None:
        """
        Assert that the ``do_retry`` method returns the return value of the
        callable on a successful call of the callable.
        """

        assert self._instance.do_retry(lambda: 10 + 5) == 15
        assert self._instance.do_retry(lambda: "Hello World") == "Hello World"
