from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar

_IN = TypeVar("_IN")
_RT = TypeVar("_RT")


class Task(Generic[_IN, _RT], metaclass=ABCMeta):
    """A job or action to perform.

    An interface that describes a job or action to be performed. The interface
    defines a single method :meth:`execute`, that accepts a single input value
    and returns a result. A `Task` instance can also be used as a callable, the
    actual call is delegated to `self.execute` method.
    """

    __slots__ = ()

    def __call__(self, an_input: _IN) -> _RT:
        """Perform a computation given an input and return a result.

        Call the `Task` as a callable. Delegate actual call to :meth:`execute`.

        :param an_input: An input to the task.

        :return: The result of the computation.
        """
        return self.execute(an_input)

    @abstractmethod
    def execute(self, an_input: _IN) -> _RT:
        """Perform a computation given an input and return a result.

        :param an_input: An input to the task.

        :return: The result of the computation.
        """
        ...


class TaskWithOptionalInput(
    Task[_IN | None, _RT], Generic[_IN, _RT], metaclass=ABCMeta,
):

    __slots__ = ()

    def __call__(self, an_input: _IN | None = None) -> _RT:
        return self.execute(an_input)

    @abstractmethod
    def execute(self, an_input: _IN | None = None) -> _RT:
        ...
