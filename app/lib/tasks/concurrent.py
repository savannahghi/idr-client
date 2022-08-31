from concurrent.futures import Executor, Future, ThreadPoolExecutor
from functools import reduce
from logging import getLogger
from typing import (
    Any,
    Callable,
    Generic,
    MutableSequence,
    Optional,
    Sequence,
    TypeVar,
)

from app.core import Disposable, IDRClientException, Task

# =============================================================================
# TYPES
# =============================================================================


_IN = TypeVar("_IN")

_RT = TypeVar("_RT")

Accumulator = Callable[
    [MutableSequence[Future[_RT]], _RT], MutableSequence[Future[_RT]]
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
    Checks if a :class:`future <Future>` completed successfully and returns
    ``True`` if so and ``False`` otherwise. In this context a *future* is
    considered to have completed successfully if it wasn't cancelled and no
    exception was raised on it's callee.

    :param future: A future instance to check for successful completion.

    :return: ``True` if the future completed successfully, ``False`` otherwise.
    """
    return bool(
        future.done() and not future.cancelled() and future.exception() is None
    )


class ConcurrentExecutorDisposedError(IDRClientException):
    """
    An exception indicating that an erroneous usage of a disposed
    :class:`concurrent executor <ConcurrentExecutor>` was made.
    """

    def __init__(
        self, message: Optional[str] = "ConcurrentExecutor disposed."
    ):
        super().__init__(message=message)


# =============================================================================
# TASK
# =============================================================================


class ConcurrentExecutor(
    Generic[_IN, _RT], Task[_IN, MutableSequence[Future[_RT]]], Disposable
):
    def __init__(
        self,
        *tasks: Task[_IN, _RT],
        accumulator: Optional[Accumulator] = None,
        initial_value: Optional[MutableSequence[Future[_RT]]] = None,
        executor: Optional[Executor] = None,
    ):
        self._tasks: Sequence[Task[_IN, _RT]] = tuple(tasks)  # TODO: queue??
        self._accumulator: Accumulator = (
            accumulator or self._default_accumulator
        )
        self._initial_value: MutableSequence[Future[_RT]]
        self._initial_value = initial_value or list()
        self._executor: Executor = executor or ThreadPoolExecutor()
        self._is_disposed: bool = False

    def __enter__(self) -> "ConcurrentExecutor":
        self._ensure_not_disposed()
        return self

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed

    @property
    def tasks(self) -> Sequence[Task[_IN, _RT]]:
        return self._tasks

    def dispose(self) -> None:
        self._executor.shutdown(wait=True)
        self._is_disposed = True

    def execute(self, an_input: _IN) -> MutableSequence[Future[_RT]]:
        self._ensure_not_disposed()
        return reduce(
            lambda _partial, _tsk: self._accumulator(
                _partial,
                self._executor.submit(self._do_execute_task, _tsk, an_input),
            ),
            self.tasks,
            self._initial_value,
        )

    def _ensure_not_disposed(self) -> None:
        if self._is_disposed:
            raise ConcurrentExecutorDisposedError()

    @staticmethod
    def _default_accumulator(
        partial_results: MutableSequence[Future[_RT]], task_output: Future[_RT]
    ) -> MutableSequence[Future[_RT]]:
        partial_results.append(task_output)
        return partial_results

    @staticmethod
    def _do_execute_task(task: Task[_IN, _RT], an_input: _IN) -> _RT:
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
