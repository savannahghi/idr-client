from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar

IN = TypeVar("IN")
RT = TypeVar("RT")


class Task(Generic[IN, RT], metaclass=ABCMeta):
    """Interface that describes a job or action to perform."""

    @abstractmethod
    def execute(self, an_input: IN) -> RT:
        """Perform a computation given an input and return a result.

        :param an_input: An input to the task.
        :return: The result of the computation.
        """
        ...
