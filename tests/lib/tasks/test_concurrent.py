from concurrent.futures import Executor, ThreadPoolExecutor, wait
from typing import Sequence
from unittest import TestCase

import pytest

from app.core import Task
from app.lib import ConcurrentExecutor, completed_successfully
from app.lib.tasks.concurrent import ConcurrentExecutorDisposedError

# =============================================================================
# HELPERS
# =============================================================================


class _AddOne(Task[int, int]):
    """
    A simple task that takes an integer and returns the sum of the integer
    and 1.
    """

    def execute(self, an_input: int) -> int:
        return an_input + 1


class _DivideByZero(Task[int, int]):
    """
    A simple task that always fails because it divides it's input by zero.
    """

    def execute(self, an_input: int) -> int:
        return int(an_input / 0)


class _IntToString(Task[int, str]):
    """
    A simple task that takes an integer and returns the integer's string
    representation.
    """

    def execute(self, an_input: int) -> str:
        return str(an_input)


# =============================================================================
# TEST CASES
# =============================================================================


class TestConcurrentExecutor(TestCase):
    """Tests for the ``ConcurrentExecutor`` class."""

    def setUp(self) -> None:
        super().setUp()
        self._tasks: Sequence[_AddOne] = tuple(_AddOne() for _ in range(10))
        self._instance: ConcurrentExecutor[int, int] = ConcurrentExecutor(
            *self._tasks
        )

    def tearDown(self) -> None:
        super().tearDown()
        self._instance.dispose()

    def test_dispose_method_idempotency(self) -> None:
        """
        Assert that the ``dispose`` method can be called multiple times without
        failing.
        """
        # Call the dispose method 10 times
        for _ in range(10):
            self._instance.dispose()

        assert self._instance.is_disposed

    def test_dispose_method_side_effects(self) -> None:
        """
        Assert the ``dispose``method shutdowns the embedded
        `:class:executor <concurrent.futures.Executor>` instance and marks the
        instance as disposed.
        """
        executor_service: Executor = ThreadPoolExecutor()
        instance: ConcurrentExecutor[int, str] = ConcurrentExecutor(
            _IntToString(), _IntToString(), executor=executor_service
        )
        instance.dispose()

        assert instance.is_disposed
        # A shutdown executor service should raise a RunTimeError on attempted
        # usage.
        with pytest.raises(RuntimeError):
            executor_service.submit(_AddOne().execute, 1)

    def test_execute_method_return_value(self) -> None:
        """
        Assert that the execute method returns the expected value.
        """
        results1 = self._instance.execute(0)
        results2 = ConcurrentExecutor(
            _DivideByZero(), _DivideByZero()
        ).execute(1)
        result3 = ConcurrentExecutor(
            *(_IntToString() for _ in range(10))
        ).execute(10)

        for result in results1:
            assert result.result() == 1
            assert result.done()
        for result in results2:
            assert isinstance(result.exception(), ZeroDivisionError)
            assert result.done()
        for result in result3:
            assert result.result() == "10"
            assert result.done()

    def test_is_dispose_property_return_value(self) -> None:
        """Assert the ``is_disposed`` property returns the expected result."""
        instance: ConcurrentExecutor[int, str] = ConcurrentExecutor(
            _IntToString(), _IntToString()
        )
        instance.dispose()

        assert instance.is_disposed
        assert not self._instance.is_disposed

    def test_tasks_return_value(self) -> None:
        """
        Assert that the ``tasks`` property returns the expected result. The
        property should return a sequence of the same tasks given to the
        instance during initialization.
        """
        self.assertTupleEqual(tuple(self._tasks), tuple(self._instance.tasks))

    def test_using_a_disposed_executor_raises_expected_errors(self) -> None:
        """
        Assert that using a disposed concurrent executor instance results in
        ``ConcurrentExecutorDisposedError`` being raised.
        """
        self._instance.dispose()
        with pytest.raises(ConcurrentExecutorDisposedError):
            self._instance.execute(10)


class TestConcurrentModule(TestCase):
    """Tests for the ``app.lib.concurrent`` module globals."""

    def setUp(self) -> None:
        super().setUp()
        self._erroneous_tasks: Sequence[_DivideByZero] = tuple(
            _DivideByZero() for _ in range(10)
        )
        self._valid_tasks: Sequence[_AddOne] = tuple(
            _AddOne() for _ in range(15)
        )

    def test_completed_successfully_function_return_value(self) -> None:
        """
        Assert that the ``completed_successfully`` function returns the
        expected value.
        """

        with ConcurrentExecutor(*self._erroneous_tasks) as c:
            results1 = c.execute(10)
            wait(results1)
        with ConcurrentExecutor(*self._valid_tasks) as c:
            results2 = c.execute(1)
            wait(results2)
        with ConcurrentExecutor(
            *(tuple(self._erroneous_tasks) + tuple(self._valid_tasks))
        ) as c:
            results3 = c.execute(1)
            wait(results3)

        for result in results1:
            assert not completed_successfully(result)
        for result in results2:
            assert completed_successfully(result)
        assert len(tuple(filter(completed_successfully, results3))) == 15
        assert (
            len(
                tuple(
                    filter(lambda _r: not completed_successfully(_r), results3)
                )
            )
            == 10
        )
