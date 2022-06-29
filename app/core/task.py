from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar

IN = TypeVar("IN")
RT = TypeVar("RT")


class Task(Generic[IN, RT], metaclass=ABCMeta):
    """Interface that describes a job or action to perform."""

    def __call__(self, an_input: IN) -> RT:
        """
        Allow calling tasks as callables.

        Delegates actual call to `self.execute`.
        """
        return self.execute(an_input)

    @abstractmethod
    def execute(self, an_input: IN) -> RT:
        """Perform a computation given an input and return a result.

        :param an_input: An input to the task.
        :return: The result of the computation.
        """
        ...
