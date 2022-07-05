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
# ITEM PROCESSORS
# =============================================================================


class Chainable(
    Generic[_IN, _RT], Task[Callable[[_IN], _RT], "Chainable[_RT, Any]"]
):
    def __init__(self, an_input: _IN):
        self._an_input: _IN = an_input

    @property
    def an_input(self) -> _IN:
        return self._an_input

    def execute(self, bind: Callable[[_IN], _RT]) -> "Chainable[_RT, Any]":
        from app.lib import ensure_not_none

        ensure_not_none(bind, '"bind" cannot be None.')
        return Chainable(bind(self.an_input))


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


class Consumer(Generic[_IN], Task[_IN, _IN]):
    def __init__(self, consume: Callable[[_IN], None]):
        from app.lib import ensure_not_none

        ensure_not_none(consume, "consume cannot be None.")
        self._consume: Callable[[_IN], None] = consume

    def execute(self, an_input: _IN) -> _IN:
        self._consume(an_input)
        return an_input


class Pipeline(Generic[_IN, _RT], Task[_IN, _RT]):
    def __init__(self, *tasks: Task[Any, Any]):
        from app.lib import ensure_not_none_nor_empty

        ensure_not_none_nor_empty(tasks, "tasks cannot be None or empty.")
        self._tasks: Sequence[Task[Any, Any]] = tuple(tasks)

    @property
    def tasks(self) -> Sequence[Task[Any, Any]]:
        return self._tasks

    def execute(self, an_input: _IN) -> _RT:
        _acc: Any
        _tsk: Task[Any, Any]
        return cast(
            _RT,
            reduce(
                lambda _acc, _tsk: _tsk.execute(_acc),
                self.tasks[1:],
                self.tasks[0].execute(an_input),
            ),
        )
