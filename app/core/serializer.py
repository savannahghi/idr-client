from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar

N = TypeVar("N")  # Native Type
S = TypeVar("S")  # Serialized Type


class Serializer(Generic[N, S], metaclass=ABCMeta):
    """
    Interface describing objects that can transform other objects to formats
    different from their native formats to facilitate transmission or storage.
    """

    @abstractmethod
    def serialize(self, value: N) -> S:
        ...

    @abstractmethod
    def deserialize(self, data: S) -> N:
        ...
