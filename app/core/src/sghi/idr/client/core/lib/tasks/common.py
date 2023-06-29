from collections.abc import Callable, Sequence
from functools import reduce
from typing import Any, Generic, TypeVar, cast

from sghi.idr.client.core.task import Task

# =============================================================================
# TYPES
# =============================================================================


_IN = TypeVar("_IN")
_RT = TypeVar("_RT")


# =============================================================================
# ITEM PROCESSORS
# =============================================================================


class Chainable(
    Generic[_IN, _RT],
    Task[Callable[[_IN], _RT], "Chainable[_RT, Any]"],
):
    def __init__(self, value: _IN):
        super().__init__()
        self._value: _IN = value

    @property
    def value(self) -> _IN:
        return self._value

    def execute(
        self,
        an_input: Callable[[_IN], _RT],
    ) -> "Chainable[_RT, Any]":
        from sghi.idr.client.core.lib import ensure_not_none

        ensure_not_none(an_input, '"bind" cannot be None.')
        return Chainable(an_input(self._value))


class Consumer(Generic[_IN], Task[_IN, _IN]):
    def __init__(self, consume: Callable[[_IN], None]):
        super().__init__()
        from sghi.idr.client.core.lib import ensure_not_none

        ensure_not_none(consume, "consume cannot be None.")
        self._consume: Callable[[_IN], None] = consume

    def execute(self, an_input: _IN) -> _IN:
        self._consume(an_input)
        return an_input


class Pipeline(Generic[_IN, _RT], Task[_IN, _RT]):
    def __init__(self, *tasks: Task[Any, Any]):
        super().__init__()
        from sghi.idr.client.core.lib import ensure_not_none_nor_empty

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