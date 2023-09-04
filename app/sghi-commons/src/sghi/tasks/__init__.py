"""
Task interface definition together with its common implementations.
"""
from __future__ import annotations

import warnings
from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Iterable, MutableSequence, Sequence
from concurrent.futures import (
    ALL_COMPLETED,
    Executor,
    Future,
    ThreadPoolExecutor,
    wait,
)
from functools import reduce
from logging import Logger, getLogger
from typing import Any, Generic, Self, TypeVar, cast

from ..disposable import Disposable, ResourceDisposedError
from ..disposable import not_disposed as _nd_factory
from ..utils import ensure_not_none, ensure_not_none_nor_empty, type_fqn

# =============================================================================
# TYPES
# =============================================================================


_IT = TypeVar("_IT")
_OT = TypeVar("_OT")
_OT1 = TypeVar("_OT1")


# =============================================================================
# HELPERS
# =============================================================================


def _callables_to_tasks_as_necessary(
    tasks: Sequence[Task[_IT, _OT] | Callable[[_IT], _OT]],
) -> Sequence[Task[_IT, _OT]]:
    """Convert callables to :class:`Task` instances if necessary.

    The given callables should accept a single parameter of type ``IT`` and
    return a value of type ``OT``. Instances of ``Tasks`` in the given
    ``Sequence`` will be returned as is.

    :param tasks: A ``Sequence`` of ``Task`` instances or callables.

    :return: A ``Sequence`` of ``Task`` instances.

    :raises ValueError: If `tasks` is ``None``.
    """
    ensure_not_none(tasks, "'tasks' MUST not be None.")
    return tuple(
        task if isinstance(task, Task) else Task.of_callable(task)
        for task in tasks
    )


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


# =============================================================================
# EXCEPTIONS
# =============================================================================


class ConcurrentExecutorDisposedError(ResourceDisposedError):
    """
    Indicates that an erroneous usage of a disposed :class:`ConcurrentExecutor`
    was made.
    """

    def __init__(self, message: str | None = "ConcurrentExecutor disposed."):
        """
        Initialize a ``ConcurrentExecutorDisposedError`` with an optional
        message.

        :param message: An optional message for the exception.
        """
        super().__init__(message=message)


not_disposed = _nd_factory(exc_factory=ConcurrentExecutorDisposedError)


# =============================================================================
# TASK INTERFACE
# =============================================================================


class Task(Generic[_IT, _OT], metaclass=ABCMeta):
    """A job or action to perform.

    An interface that describes a job or action to be performed. The interface
    defines a single method :meth:`execute`, that accepts a single input value
    and returns a result. A `Task` instance can also be used as a callable, the
    actual call is delegated to the ``execute`` method.
    """

    __slots__ = ()

    def __call__(self, an_input: _IT) -> _OT:
        """Perform a computation given an input and return a result.

        Call the ``Task`` as a callable. Delegate actual call to
        :meth:`execute`.

        :param an_input: An input to the tasks.

        :return: The result of the computation.
        """
        return self.execute(an_input)

    @abstractmethod
    def execute(self, an_input: _IT) -> _OT:
        """Perform a computation given an input and return a result.

        :param an_input: An input to the task.

        :return: The result of the computation.
        """
        ...

    @staticmethod
    def of_callable(source_callable: Callable[[_IT], _OT]) -> Task[_IT, _OT]:
        """Create a :class:`Task` instance from a callable.

        .. note::

            The given callable *MUST* accept exactly one parameter.

        :param source_callable: The callable function to wrap as a ``Task``.
            This *MUST* not be ``None``.

        :return: A ``Task`` instance.

        :raises ValueError: If `source_callable` is ``None``.
        """
        return _OfCallable(source_callable=source_callable)


# =============================================================================
# COMMON IMPLEMENTATIONS
# =============================================================================


class Chain(Task[Callable[[_IT], Any], "Chain[Any]"], Generic[_IT]):
    """
    A :class:`Task` that wraps a value and applies a transformation (or series
    of transformations) on the value.

    The output of each transformation is wrapped in a new ``Chain`` instance,
    facilitating the chaining together of multiple transformations. This
    capability can be employed to compose complex transformations from smaller
    ones.

    The wrapped value can be retrieved using the :attr:`value` property.
    """

    __slots__ = ("_value",)

    def __init__(self, value: _IT) -> None:
        """Initialize a new :class:`Chain` instance that wraps the given value.

        :param value: The value to wrap and apply transformations to.
        """
        super().__init__()
        self._value: _IT = value

    @property
    def value(self) -> _IT:
        """Return the wrapped value.

        :return: The wrapped value.
        """
        return self._value

    def execute(self, an_input: Callable[[_IT], _OT]) -> Chain[_OT]:
        """
        Perform the given transformation on the wrapped value and wrap the
        result in a new ``Chain`` instance.

        :param an_input: A callable defining a transformation to be applied to
            the wrapped value. This MUST not be ``None``.

        :return: A new ``Chain`` instance that wraps the result of the given
            transformation.

        :raises ValueError: If the given transformation is ``None``.
        """
        bind: Callable[[_IT], _OT]
        bind = ensure_not_none(an_input, "'an_input' MUST not be None.")
        return Chain(bind(self._value))


class Consume(Task[_IT, None], Generic[_IT]):
    """A :class:`Task` that applies an action to it's inputs.

    This ``Task`` wraps a callable and applies it to its inputs. It does not
    produce any output and is better suited for operations with side effects.

    :param accept: The callable function to apply to the input.
    :return: A Consume task.
    """

    __slots__ = ("_accept",)

    def __init__(self, accept: Callable[[_IT], Any]) -> None:
        """
        Initialize a new :class:`Consume` instance that applies the given
        action to it's inputs.

        :param accept: A callable to apply to this task's inputs. This MUST not
            be None.

        :raises ValueError: If the given callable is ``None``.
        """
        super().__init__()
        ensure_not_none(accept, "'accept' MUST not be None.")
        self._accept: Callable[[_IT], Any] = accept

    def and_then(self, accept: Callable[[_IT], Any]) -> Consume[_IT]:
        """Compose this :class:`Consume` action with the provided action.

        This creates a new ``Consume`` instance that performs both this task's
        action and the provided action.

        :param accept: The action to compose with this task's action. This
            MUST be not None.

        :return: A new ``Consume`` instance that performs both actions.

        :raises ValueError: If the given callable is ``None``.
        """
        ensure_not_none(accept, "'accept' MUST not be None.")

        def _compose_accept(an_input: _IT) -> None:
            self._accept(an_input)
            accept(an_input)
        return Consume(accept=_compose_accept)

    def execute(self, an_input: _IT) -> None:
        self._accept(an_input)
        return


class Pipe(Task[_IT, _OT], Generic[_IT, _OT]):
    """A :class:`Task` that pipes its input through a ``Sequence`` of tasks.

    This ``Task`` applies a series of tasks to its input, passing the output of
    one ``Task`` as the input to the next.
    """

    __slots__ = ("_tasks",)

    def __init__(self, *tasks: Task[Any, Any] | Callable[[Any], Any]):
        """Create a new :class:`Pipe` instance of the given tasks.

        :param tasks: A ``Sequence`` of the tasks to apply this pipe's inputs
            to. This MUST not be empty.

        :raises ValueError: If no tasks were specified, i.e. ``tasks`` is
            empty.
        """
        super().__init__()
        ensure_not_none_nor_empty(tasks, "'tasks' MUST not be None or empty.")
        self._tasks: Sequence[Task[Any, Any]]
        self._tasks = _callables_to_tasks_as_necessary(tasks)

    @property
    def tasks(self) -> Sequence[Task[Any, Any]]:
        """The ``Sequence`` of :class:`tasks <Tasks>` that comprise this pipe.

        :return: The tasks that comprise this pipe.
        """
        return self._tasks

    def execute(self, an_input: _IT) -> _OT:
        """
        Apply the given input to the :class:`tasks <Task>` that comprise this
        pipe, sequentially.

        The output of each task becomes the input of the next one. The result
        of the final ``Task`` is the output of this *pipe* operation.

        :param an_input: The input to start with.

        :return: The final output after applying all the tasks.
        """
        _acc: Any
        _tsk: Task[Any, Any]
        return cast(
            _OT,
            reduce(
                lambda _acc, _tsk: _tsk(_acc),
                self.tasks[1:],
                self.tasks[0](an_input),
            ),
        )


chain = Chain

consume = Consume

pipe = Pipe


# =============================================================================
# CONCURRENT EXECUTOR
# =============================================================================


class ConcurrentExecutor(
    Task[_IT, Iterable[Future[_OT]]],
    Disposable,
    Generic[_IT, _OT],
):
    """
    A :class:`Task` that concurrently executes multiple `tasks` with a shared
    input.

    The output of these tasks is an :class:`Iterable` of
    :external+python:py:class:`futures<concurrent.futures.Future>`
    representing the execution of the given tasks. If the
    ``wait_for_completion`` constructor parameter is set to ``True``, the
    default, the `execute` method will block until all tasks have completed.

    .. important::

        When ``wait_for_completion`` is set to ``False``, instances of this
        class should not be used as context managers. This is because the
        underlying ``Executor`` will be shutdown immediately once ``execute``
        returns.

    .. tip::

        By default, this tasks uses a
        :external+python:py:class:`~concurrent.futures.ThreadPoolExecutor`
        to run the tasks concurrently. This is suitable for short `I/O-bound`
        tasks. However, for compute-intensive tasks, consider using a
        :external+python:py:class:`~concurrent.futures.ProcessPoolExecutor` by
        passing it through the ``executor`` constructor parameter during
        initialization.

        For more details, see the official Python
        :doc:`concurrency docs <python:library/concurrent.futures>`.
    """

    __slots__ = (
        "_tasks",
        "_wait_for_completion",
        "_initial_value",
        "_executor",
        "_is_disposed",
        "_logger",
    )

    def __init__(
            self,
            *tasks: Task[_IT, _OT] | Callable[[_IT], _OT],
            wait_for_completion: bool = True,
            executor: Executor | None = None,
    ):
        """
        Initialize a new `ConcurrentExecutor` instance with the given
        properties.

        :param tasks: The tasks to be executed concurrently. This MUST not be
            ``None`` or empty.
        :param wait_for_completion: Whether ``execute`` should block and wait
            for all the given tasks to complete execution. Defaults to
            ``True``.
        :param executor: The :class:`executor <concurrent.futures.Executor>`
            instance to use when executing the tasks. If not provided, a
            ``ThreadPoolExecutor`` is used.

        :raises ValueError: If tasks is ``None`` or empty.
        """
        super().__init__()
        ensure_not_none_nor_empty(tasks, "'tasks' MUST not be None or empty.")
        self._tasks: Sequence[Task[_IT, _OT]]
        self._tasks = _callables_to_tasks_as_necessary(tasks)
        self._wait_for_completion: bool = wait_for_completion
        self._executor: Executor = executor or ThreadPoolExecutor()
        self._initial_value: MutableSequence[Future[_OT]] = []
        self._is_disposed: bool = False
        self._logger: Logger = getLogger(type_fqn(self.__class__))

    @not_disposed
    def __enter__(self) -> Self:
        super().__enter__()
        if not self._wait_for_completion:
            msg: str = (
                "Using instances of this class as a context manager when "
                "'wait_for_completion' is set to 'False' is discouraged."
            )
            warnings.warn(message=msg, stacklevel=3)
        return self

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed

    @property
    def tasks(self) -> Sequence[Task[_IT, _OT]]:
        """
        Get the sequence of :class:`tasks<Task>` that will be executed
        concurrently.

        :return: The sequence of tasks.
        """
        return self._tasks

    def dispose(self) -> None:
        self._executor.shutdown(wait=self._wait_for_completion)
        self._is_disposed = True

    @not_disposed
    def execute(self, an_input: _IT) -> Iterable[Future[_OT]]:
        """Execute the tasks concurrently with the given input.

        .. note::

            If the ``wait_for_completion`` property is ``True``, this method
            will block until all tasks finish execution. If set to ``False``,
            all tasks will be scheduled for concurrent execution, after which
            this method will return immediately, regardless of whether all
            tasks have completed execution.

        :param an_input: The shared input to pass to each tasks.

        :return: An ``Iterable`` of futures representing the execution of each
            tasks.

        :raises ConcurrentExecutorDisposedError: If this executor is already
            disposed.
        """
        futures: Iterable[Future[_OT]] = tuple(
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
        partial_results: MutableSequence[Future[_OT]],
        task_output: Future[_OT],
    ) -> MutableSequence[Future[_OT]]:
        partial_results.append(task_output)
        return partial_results

    def _do_execute_task(self, task: Task[_IT, _OT], an_input: _IT) -> _OT:
        """Execute an individual :class:`.Task` with the provided input.

        :param task: The ``Task`` to execute.
        :param an_input: The input to pass to the ``Task``.

        :return: The result of the tasks's execution.

        :raises Exception: If the tasks execution encounters an exception.
        """
        try:
            result: _OT = task(an_input)
        except Exception as exp:
            self._logger.error(
                "Error while executing tasks of type='%s'.",
                type_fqn(task),
                exc_info=exp,
            )
            raise exp
        return result


execute_concurrently = ConcurrentExecutor


# =============================================================================
# FROM CALLABLE
# =============================================================================


class _OfCallable(Task[_IT, _OT]):

    __slots__ = ("_source_callable",)

    def __init__(self, source_callable: Callable[[_IT], _OT]):
        super().__init__()
        ensure_not_none(source_callable, "'source_callable' MUST not be None.")
        self._source_callable: Callable[[_IT], _OT]
        self._source_callable = source_callable

    def execute(self, an_input: _IT) -> _OT:
        return self._source_callable(an_input)


# =============================================================================
# MODULE EXPORTS
# =============================================================================


__all__ = [
    "Chain",
    "ConcurrentExecutor",
    "ConcurrentExecutorDisposedError",
    "Consume",
    "Pipe",
    "Task",
    "chain",
    "consume",
    "execute_concurrently",
    "pipe",
]
