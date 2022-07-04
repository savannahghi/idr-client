from typing import Callable
from unittest import TestCase

import pytest

from app.core import Task
from app.lib import Chainable, Consumer, Pipeline

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


class TestChainable(TestCase):
    """Tests for the :class:`Chainable` class."""

    def setUp(self) -> None:
        super().setUp()
        self._an_input: int = 0
        self._chainable: Chainable = Chainable(an_input=self._an_input)
        self._add_one: Callable[[int], int] = lambda _x: _x + 1
        self._int_to_str: Callable[[int], str] = lambda _x: str(_x)

    def test_execution(self) -> None:
        val: str = (
            self._chainable.execute(self._add_one)
            .execute(self._add_one)
            .execute(self._add_one)
            .execute(self._add_one)
            .execute(self._add_one)
            .execute(self._int_to_str)
            .an_input
        )
        assert val == "5"

    def test_execution_input_must_not_be_none(self) -> None:
        """
        Assert that the input to :meth:`~Chainable.execute()` must not be
        ``None``.
        """
        with pytest.raises(ValueError):
            self._chainable.execute(None)  # type: ignore


class TestConsumer(TestCase):
    """Tests for the :class:`Consumer` class."""

    def setUp(self) -> None:
        super().setUp()
        self._global_state: int = 5
        self._consumer: Consumer[int] = Consumer(consume=self._consume)

    def test_execution(self) -> None:
        out: int = self._consumer(5)  # noqa

        assert self._global_state == 10
        assert out == 5

    def test_consume_constructor_arg_must_not_be_none(self) -> None:
        """
        Assert that the ``consume`` argument to the constructor must not be
        ``None``.
        """
        with pytest.raises(ValueError):
            Consumer(consume=None)  # type: ignore

    def _consume(self, an_input: int) -> None:
        """Update the global state by adding the given value."""
        self._global_state += an_input


class TestPipeline(TestCase):
    """Tests for the :class:`Pipeline` class."""

    def setUp(self) -> None:
        super().setUp()
        self._an_input: int = 0
        self._global_state: int = 5
        self._consumer: Consumer[int] = Consumer(consume=self._consume)
        self._pipeline: Pipeline[int, str] = Pipeline(
            _AddOne(),
            _AddOne(),
            self._consumer,
            _AddOne(),
            _AddOne(),
            _AddOne(),
            self._consumer,
            _IntToString(),
        )

    def test_execution(self) -> None:
        val: str = self._pipeline(self._an_input)  # noqa

        assert val == "5"
        assert self._global_state == 12

    def test_that_a_pipeline_must_contains_at_least_one_task(self) -> None:
        """
        Assert that a pipeline must contain one or more tasks to be valid.
        """
        with pytest.raises(ValueError):
            Pipeline()

    def _consume(self, an_input: int) -> None:
        """Update the global state by adding the given value."""
        self._global_state += an_input
