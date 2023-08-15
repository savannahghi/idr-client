from __future__ import annotations

from collections.abc import Callable, Iterable, MutableSequence, Sequence
from concurrent.futures import (
    ALL_COMPLETED,
    Executor,
    Future,
    ThreadPoolExecutor,
    wait,
)
from functools import reduce
from logging import getLogger
from typing import Any, Generic, TypeVar

from ..disposable import Disposable, ResourceDisposedError
from ..disposable import not_disposed as _rr_factory
from .task import Task

# =============================================================================
# TYPES
# =============================================================================


_IN = TypeVar("_IN")

_RT = TypeVar("_RT")

Accumulator = Callable[
    [MutableSequence[Future[_RT]], Future[_RT]],
    MutableSequence[Future[_RT]],
]

# =============================================================================
# CONSTANTS
# =============================================================================


_LOGGER = getLogger(__name__)


# =============================================================================
# HELPERS
# =============================================================================


def completed_successfully(future: Future[Any]) -> bool:
    """
    Check if a :external+python:py:class:`~concurrent.futures.Future` completed
    successfully and return ``True`` if so, or ``False`` otherwise.

    In this context, a ``Future`` is considered to have completed successfully
    if it wasn't canceled and no uncaught exceptions were raised by its callee.

    :param future: A ``Future`` instance to check for successful completion.

    :return: ``True`` if the future completed successfully, ``False``
        otherwise.
    """
    return bool(
        future.done()
        and not future.cancelled()
        and future.exception() is None,
    )


class ConcurrentExecutorDisposedError(ResourceDisposedError):
    """
    Indicates that an erroneous usage of a disposed :class:`ConcurrentExecutor`
    was made.
    """

    def __init__(self, message: str | None = "ConcurrentExecutor disposed."):
        super().__init__(message=message)


_requires_resource = _rr_factory(exc_factory=ConcurrentExecutorDisposedError)


# =============================================================================
# TASK
# =============================================================================


class ConcurrentExecutor(
    Task[_IN, Iterable[Future[_RT]]],
    Disposable,
    Generic[_IN, _RT],
):
    """
    A :class:`.Task` that concurrently executes multiple `tasks` with a shared
    input.

    The output of the task is an :class:`Iterable` of
    :external+python:py:class:`futures<concurrent.futures.Future>`
    representing the execution of the given tasks. If the
    ``wait_for_completion`` constructor parameter is set to ``True``, the
    `execute` method will block until all tasks have completed.

    .. tip::
        By default, this task uses a
        :external+python:py:class:`~concurrent.futures.ThreadPoolExecutor`
        to run the tasks concurrently. This is suitable for short `I/O-bound`
        tasks. However, for compute-intensive tasks, consider using a
        :external+python:py:class:`~concurrent.futures.ProcessPoolExecutor` by
        passing it through the ``executor`` constructor parameter during
        initialization.

        For more details, see the official Python
        :doc:`concurrency docs <python:library/concurrent.futures>`.
    """

    def __init__(
        self,
        *tasks: Task[_IN, _RT],
        wait_for_completion: bool = False,
        executor: Executor | None = None,
    ):
        """
        Initialize a new `ConcurrentExecutor` instance with the given
        properties.

        :param tasks: The tasks to be executed concurrently.
        :param wait_for_completion: Whether to wait for the given tasks to
            complete once ``execute`` is called. Defaults to ``False``.
        :param executor: The :class:`executor <concurrent.futures.Executor>`
            instance to use when executing the tasks. If not provided, a
            ``ThreadPoolExecutor`` is used.
        """
        super().__init__()
        self._tasks: Sequence[Task[_IN, _RT]] = tuple(tasks)
        self._wait_for_completion: bool = wait_for_completion
        self._initial_value: MutableSequence[Future[_RT]] = []
        self._executor: Executor = executor or ThreadPoolExecutor()
        self._is_disposed: bool = False

    @_requires_resource
    def __enter__(self) -> ConcurrentExecutor:
        super().__enter__()
        return self

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed

    @property
    def tasks(self) -> Sequence[Task[_IN, _RT]]:
        """
        Get the sequence of :class:`tasks<.Task>` that will be executed
        concurrently.

        :return: The sequence of tasks.
        """
        return self._tasks

    def dispose(self) -> None:
        self._executor.shutdown(wait=True)
        self._is_disposed = True

    @_requires_resource
    def execute(self, an_input: _IN) -> Iterable[Future[_RT]]:
        """Execute the tasks concurrently with the given input.

        .. note::

            If the ``wait_for_completion`` constructor parameter was set to
            ``True`` at initialization, this method will block until all tasks
            complete.

        :param an_input: The shared input to pass to each task.

        :return: An ``Iterable`` of futures representing the execution of each
            task.
        """
        futures: Iterable[Future[_RT]] = tuple(
            reduce(
                lambda _partial, _tsk: self._accumulate(
                    _partial,
                    self._executor.submit(
                        self._do_execute_task,
                        _tsk,
                        an_input,
                    ),
                ),
                self.tasks,
                self._initial_value,
            ),
        )
        if self._wait_for_completion:
            wait(futures, return_when=ALL_COMPLETED)
        return futures

    @staticmethod
    def _accumulate(
        partial_results: MutableSequence[Future[_RT]],
        task_output: Future[_RT],
    ) -> MutableSequence[Future[_RT]]:
        partial_results.append(task_output)
        return partial_results

    @staticmethod
    def _do_execute_task(task: Task[_IN, _RT], an_input: _IN) -> _RT:
        """Execute an individual :class:`.Task` with the provided input.

        :param task: The ``Task`` to execute.
        :param an_input: The input to pass to the ``Task``.

        :return: The result of the task's execution.

        :raises Exception: If the task execution encounters an exception.
        """
        try:
            result: _RT = task.execute(an_input)
        except Exception as exp:
            _LOGGER.error(
                'Error while executing task of type="%s.%s".',
                task.__module__,
                task.__class__.__name__,
                exc_info=exp,
            )
            raise exp
        return result
