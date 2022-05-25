from abc import ABCMeta, abstractmethod
from typing import Any, Mapping


class InitFromMapping(metaclass=ABCMeta):

    @classmethod
    @abstractmethod
    def of_mapping(cls, mapping: Mapping[str, Any]) -> object:
        ...
