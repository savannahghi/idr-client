from abc import ABCMeta, abstractmethod
from typing import Generic, Sequence, Type, TypeVar

from typing_inspect import is_optional_type

from .mixins import InitFromMapping
from .task import Task

# =============================================================================
# TYPES
# =============================================================================

_IN = TypeVar("_IN")
_RT = TypeVar("_RT")
_MD = TypeVar("_MD", bound="AbstractMetadata")


# =============================================================================
# HELPERS
# =============================================================================

def _get_required_fields_names(metadata: Type[_MD]) -> Sequence[str]:
    return tuple(
        field_name
        for field_name, field_type in metadata.__annotations__.items()
        if not is_optional_type(field_type)
    )


# =============================================================================
# METADATA
# =============================================================================

class AbstractMetadata(Generic[_IN, _RT], InitFromMapping, metaclass=ABCMeta):
    """Represents metadata needed to initialize a tasks."""

    id: str
    name: str

    def __init__(self, required_fields: Sequence[str], **kwargs):
        if any(set(required_fields).difference(set(kwargs.keys()))):
            raise ValueError(
                "The following values are required: %s" % ", ".join(
                    required_fields
                )
            )

        for valid_field in self.__annotations__.keys():
            setattr(self, valid_field, kwargs.get(valid_field))

    @abstractmethod
    def as_task(self) -> Task[_IN, _RT]:
        ...
