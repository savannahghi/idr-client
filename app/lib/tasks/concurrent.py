from functools import reduce
from typing import (
    Any,
    Callable,
    Generic,
    List,
    Optional,
    Sequence,
    TypeVar,
    cast,
)

from app.core import Task

# =============================================================================
# TYPES
# =============================================================================


_IN = TypeVar("_IN")

_RT = TypeVar("_RT")


# =============================================================================
# TASK
# =============================================================================


class ConcurrentExecutor(Generic[_IN, _RT], Task[_IN, _RT]):
    def __init__(
        self,
        *tasks: Task[Any, Any],
        accumulator: Optional[Callable[[_RT, Any], _RT]] = None,
        initial_value: _RT = cast(_RT, list()),
    ):
        self._tasks: Sequence[Task[Any, Any]] = tuple(tasks)  # TODO: queue??
        self._accumulator: Callable[[_RT, Any], _RT] = (
            accumulator or self._default_accumulator
        )
        self._initial_value: _RT = initial_value

    @property
    def tasks(self) -> Sequence[Task[Any, Any]]:
        return self._tasks

    def execute(self, an_input: _IN) -> _RT:
        # TODO: Add a proper implementation that executes the tasks
        #  concurrently.
        return reduce(
            lambda _partial, _tsk: self._accumulator(
                _partial, _tsk.execute(an_input)
            ),
            self._tasks,
            self._initial_value,
        )

    @staticmethod
    def _default_accumulator(partial_result: _RT, task_output: Any) -> _RT:
        _partial: List[Any] = list(
            # An assumption is made here that the default initial value will
            # always be a sequence of some kind.
            cast(Sequence, partial_result)
        )
        _partial.append(task_output)
        return cast(_RT, _partial)
