from abc import ABCMeta, abstractmethod
from functools import lru_cache
from typing import Any, Generic, Mapping, Optional, Sequence, Type, TypeVar

from typing_inspect import is_optional_type

# =============================================================================
# TYPES
# =============================================================================

_ADO = TypeVar("_ADO", bound="AbstractDomainObject")
_DS = TypeVar("_DS", bound="DataSource", covariant=True)


# =============================================================================
# HELPERS
# =============================================================================

@lru_cache(maxsize=None)
def _get_available_annotations(do_klass: Type[_ADO]) -> Mapping[str, Any]:
    """Extract all annotations available on a domain object class.

    This includes all annotations defined on the class's ancestors.

    *Note: The results of this method are cached to improve performance.*

    :param do_klass: A class inheriting from `AbstractDomainObject`.

    :return A mapping of the extracted annotations.
    """
    return {
        field_name: field_type
        for klass in filter(
            lambda _klass: hasattr(_klass, "__annotations__"),
            do_klass.mro()
        )
        for field_name, field_type in klass.__annotations__.items()
    }


@lru_cache(maxsize=None)
def _get_required_fields_names(do_klass: Type[_ADO]) -> Sequence[str]:
    """Determine and return the required fields of a domain object class.

    A required field in the context of this method is defined as one whose
    type is not `NoneType` or direct union with it such as `typing.Optional`.
    These includes all the fields defined on the class's ancestors.

    *Note: The results of this method are cached to improve performance.*

    :param do_klass: A class inheriting from `AbstractDomainObject`.

    :return A sequence of the required field names of a domain object class.
    """
    available_annotations: Mapping[str, Any] = _get_available_annotations(
        do_klass=do_klass
    )
    return tuple(
        field_name
        for field_name, field_type in available_annotations.items()
        if not is_optional_type(field_type)
    )


# =============================================================================
# DOMAIN ITEMS DEFINITIONS
# =============================================================================

class AbstractDomainObject(metaclass=ABCMeta):
    """The base class for all domain objects in the app."""

    def __init__(self, **kwargs):
        """
        Initialize a domain object and set the object's fields using the
        provided kwargs. Note that fields without annotations are going to be
        ignored and thus not set. If a non empty sequence of the required
        fields is returned by the `cls.get_required_fields` method, then they
        must be provided in the kwargs or else a `ValueError` exception will
        be raised.

        :param kwargs: fields and their values to set on the created object.

        :raise ValueError: if a required field isn't provided in the kwargs.
        """
        required_fields: Sequence[str] = self.__class__.get_required_fields()
        if any(set(required_fields).difference(set(kwargs.keys()))):
            raise ValueError(
                "The following values are required: %s" % ", ".join(
                    required_fields
                )
            )

        for valid_field in _get_available_annotations(self.__class__):
            setattr(self, valid_field, kwargs.get(valid_field))

    @classmethod
    def get_required_fields(cls) -> Sequence[str]:
        """Return a sequence of the required fields for this class.

        When not overriden, this method uses type annotations on the class to
        determine optional fields of the class. That is, fields whose type
        annotations aren't marked as either `NoneType` or those in direct union
        with it such as `typing.Optional`.

        :return: a sequence of the required fields for this class.
        """
        return _get_required_fields_names(cls)


class DataSource(AbstractDomainObject, metaclass=ABCMeta):
    """An interface representing an entity that contains data of interest."""
    id: str
    name: str
    description: str


class ExtractMetadata(Generic[_DS], AbstractDomainObject, metaclass=ABCMeta):
    """Metadata describing the data to be extracted from a `DataSource`."""
    id: str
    name: str
    description: str
    data_source: _DS
    preferred_uploads_name: Optional[str]
