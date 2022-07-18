from abc import ABCMeta, abstractmethod
from functools import lru_cache
from typing import Any, Generic, Mapping, Optional, Sequence, Type, TypeVar

from typing_inspect import is_optional_type

from .mixins import Disposable, InitFromMapping, ToTask

# =============================================================================
# TYPES
# =============================================================================


_ADO = TypeVar("_ADO", bound="AbstractDomainObject")
_IN = TypeVar("_IN")
_RT = TypeVar("_RT")


# =============================================================================
# HELPERS
# =============================================================================


@lru_cache(maxsize=None)
def _get_available_annotations(do_klass: Type[_ADO]) -> Mapping[str, Any]:
    """Extract all annotations available on a domain object class.

    This includes all annotations defined on the class's ancestors.

    .. note::
        The results of this method are cached to improve performance.

    :param do_klass: A class inheriting from ``AbstractDomainObject``.

    :return: A mapping of the extracted annotations.
    """
    return {
        field_name: field_type
        for klass in filter(
            lambda _klass: hasattr(_klass, "__annotations__"), do_klass.mro()
        )
        for field_name, field_type in klass.__annotations__.items()
    }


@lru_cache(maxsize=None)
def _get_required_fields_names(do_klass: Type[_ADO]) -> Sequence[str]:
    """Determine and return the required fields of a domain object class.

    A required field in the context of this method is defined as one whose
    type is not ``NoneType`` or direct union with it such as
    ``typing.Optional``. These includes all the fields defined on the class's
    ancestors.

    .. note::
        The results of this method are cached to improve performance.

    :param do_klass: A class inheriting from ``AbstractDomainObject``.

    :return: A sequence of the required field names of a domain object class.
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
        fields is returned by the
        :py:meth:`~app.core.AbstractDomainObject.get_required_fields()` method,
        then they must be provided in the kwargs or else a ``ValueError``
        exception will be raised.

        :param kwargs: fields and their values to set on the created object.

        :raise ValueError: if a required field isn't provided in the kwargs.
        """
        required_fields: Sequence[str] = self.__class__.get_required_fields()
        if any(set(required_fields).difference(set(kwargs.keys()))):
            raise ValueError(
                "The following values are required: %s"
                % ", ".join(required_fields)
            )

        for valid_field in _get_available_annotations(self.__class__):
            setattr(self, valid_field, kwargs.get(valid_field))

    @classmethod
    def get_required_fields(cls) -> Sequence[str]:
        """Return a sequence of the required fields for this class.

        When not overriden, this method uses type annotations on the class to
        determine optional fields of the class. That is, fields whose type
        annotations aren't marked as either `NoneType` or those in direct union
        with it such as ``typing.Optional``.

        :return: a sequence of the required fields for this class.
        """
        return _get_required_fields_names(cls)


class IdentifiableDomainObject(AbstractDomainObject, metaclass=ABCMeta):
    """Describes a domain object that has an id property."""

    id: str


class ExtractMetadata(
    Generic[_IN, _RT],
    IdentifiableDomainObject,
    InitFromMapping,
    ToTask[_IN, _RT],
    metaclass=ABCMeta,
):
    """
    An interface that represents metadata describing the data to be extracted
    from a :class:`DataSource`.
    """

    name: str
    description: Optional[str]
    preferred_uploads_name: Optional[str]

    def __str__(self) -> str:
        return "%s::%s" % (self.id, self.name)

    @classmethod
    def of_mapping(cls, mapping: Mapping[str, Any]) -> "ExtractMetadata":
        """
        Initialize and return an extract metadata instance from a mapping
        describing it's state.

        :param mapping: A mapping that describes the state of an extract
            metadata.

        :return: The initialized extract metadata instance.
        """
        return cls(**mapping)


class DataSource(
    IdentifiableDomainObject,
    Disposable,
    InitFromMapping,
    Generic[_RT],
    metaclass=ABCMeta,
):
    """An interface representing an entity that contains data of interest."""

    id: str
    name: str
    description: Optional[str]

    @property
    @abstractmethod
    def extract_metadata(self) -> Mapping[str, ExtractMetadata[_RT, Any]]:
        """
        Return a readonly mapping of the extract metadata instances that
        operate on this data source.

        :return: A readonly mapping of extract metadata instances that operate
            on thi data source.
        """
        ...

    @extract_metadata.setter
    @abstractmethod
    def extract_metadata(
        self, extract_metadata: Mapping[str, ExtractMetadata]
    ) -> None:
        """Set the extract metadata instances that belong to this data source.

        .. note::
            This will replace *(not update)* the current value of the extract
            metadata instances for this data source.

        :param extract_metadata: A read only mapping of the extract metadata
            instances that operate on this data source.

        :return: None.
        """
        ...

    @abstractmethod
    def get_extract_task_args(self) -> _RT:
        """
        Return an argument to be passed to an :class:`ExtractMetadata` task.

        This method is called before performing extraction for each of the
        extract metadata instances belonging to this data source.

        :return: An argument to be passed to an extract metadata task.
        """
        # TODO: Add a better API for this method.
        ...

    def __str__(self) -> str:
        return "%s::%s" % (self.id, self.name)

    @classmethod
    def of_mapping(cls, mapping: Mapping[str, Any]) -> "DataSource":
        """
        Initialize and return a data source from a mapping describing it's
        state.

        :param mapping: A mapping that describes the state of a data source.

        :return: The initialized data source instance.
        """
        return cls(**mapping)


class UploadMetadata(
    IdentifiableDomainObject, InitFromMapping, metaclass=ABCMeta
):
    """An interface that defines a data upload to an IDR Server."""


class DataSourceType(AbstractDomainObject, metaclass=ABCMeta):
    """
    An interface representing the different kinds of supported data sources.
    """

    name: str
    description: Optional[str]

    @property
    @abstractmethod
    def code(self) -> str:
        """
        Return a unique token for this data source type. This token is used
        during lookups to identify this data source type.

        :return: A unique token for this data source type.
        """
        ...

    @property
    @abstractmethod
    def data_sources(self) -> Mapping[str, DataSource]:
        """
        Return a readonly mapping of all data sources that belong to this data
        source type.

        :return: A readonly mapping of all data sources that belong to this
            data source type.
        """
        ...

    @data_sources.setter
    @abstractmethod
    def data_sources(self, data_sources: Mapping[str, DataSource]) -> None:
        """Set the data sources that belong to this data source type.

        .. note::
            This will replace *(not update)* the current value of data sources
            for this data source type.

        :param data_sources: A readonly mapping of the data sources belonging
            to this data source type.

        :return: None.
        """
        ...

    def __str__(self) -> str:
        return "%s::%s" % (self.code, self.name)

    @classmethod
    @abstractmethod
    def imp_data_source_klass(cls) -> Type[DataSource]:
        """
        Return the :class:`DataSource` concrete implementation class for this
        data source type.

        :return: The ``DataSource`` implementation for this data source type.
        """
        ...

    @classmethod
    @abstractmethod
    def imp_extract_metadata_klass(cls) -> Type[ExtractMetadata]:
        """
        Return the :class:`ExtractMetadata` concrete implementation class for
        this dats source type.

        :return: The ``ExtractMetadata`` implementation for this data source
            type.
        """
        ...
