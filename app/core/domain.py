from abc import ABCMeta, abstractmethod
from collections.abc import Mapping, Sequence
from functools import cache
from typing import Any, Generic, TypeVar

from typing_inspect import is_optional_type

from .mixins import Disposable, InitFromMapping, ToTask
from .task import Task

# =============================================================================
# TYPES
# =============================================================================


_ADO = TypeVar("_ADO", bound="AbstractDomainObject")
_IN = TypeVar("_IN")
_RT = TypeVar("_RT")


# =============================================================================
# HELPERS
# =============================================================================


@cache
def _get_available_annotations(do_klass: type[_ADO]) -> Mapping[str, Any]:
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
            lambda _klass: hasattr(_klass, "__annotations__"),
            do_klass.mro(),
        )
        for field_name, field_type in klass.__annotations__.items()
    }


@cache
def _get_required_fields_names(do_klass: type[_ADO]) -> Sequence[str]:
    """Determine and return the required fields of a domain object class.

    A required field in the context of this method is defined as one whose
    type is not ``NoneType`` or direct union with it such as
    ``typing.Optional``. These include all the fields defined on the class's
    ancestors.

    .. note::
        The results of this method are cached to improve performance.

    :param do_klass: A class inheriting from ``AbstractDomainObject``.

    :return: A sequence of the required field names of a domain object class.
    """
    available_annotations: Mapping[str, Any] = _get_available_annotations(
        do_klass=do_klass,
    )
    return tuple(
        field_name
        for field_name, field_type in available_annotations.items()
        if not is_optional_type(field_type)
    )


# =============================================================================
# DOMAIN ITEMS DEFINITIONS
# =============================================================================


class AbstractDomainObject(metaclass=ABCMeta):  # noqa: B024
    """The base class for all domain objects in the app."""

    def __init__(self, **kwargs: Any):  # noqa: ANN401
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
            err_msg: str = "The following values are required: %s" % ", ".join(
                required_fields,
            )
            raise ValueError(err_msg)

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

    id: str  # noqa: A003


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
    description: str | None
    preferred_uploads_name: str | None

    @property
    @abstractmethod
    def data_source(self) -> "DataSource":
        """
        Return the :class:`data source <DataSource>` that contains this extract
        metadata.

        :return: The data source that contains this extract metadata.
        """
        ...

    @abstractmethod
    def get_upload_meta_extra_init_kwargs(
        self,
    ) -> Mapping[str, Any] | None:
        """
        Return an optional mapping of extra keyword arguments to be used when
        initializing the :class:`upload metadata <UploadMetadata>` instance
        associated with this extract.

        :return: An optional mapping of extra keyword arguments to use when
            initializing the upload metadata instance associated with this
            extract.
        """
        return None

    @abstractmethod
    def to_task(self) -> Task[_IN, _RT]:
        """
        Return a :class:`task <Task>` that performs the actual extraction of
        data from this metadata owning :class:`data source <DataSource>`. The
        task's execute method will be given as input the return value of the
        data source's :meth:`~DataSource.get_extract_task_args()` method and
        the task's output should be the extracted data.

        :return: A task instance that extracts data from this extract metadata
            parent data source.
        """
        ...

    def __str__(self) -> str:
        return f"{self.id}::{self.name}"

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

    id: str  # noqa: A003
    name: str
    description: str | None

    @property
    @abstractmethod
    def data_source_type(self) -> "DataSourceType":
        """
        Return the :class:`data source type <DataSourceType>` that this data
        source belongs to.

        :return: The data source type that this data source belongs to.
        """
        ...

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
        self,
        extract_metadata: Mapping[str, ExtractMetadata[_RT, Any]],
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

        :raise ExtractionOperationError: If an error occurs during this
            operation.
        :raise DataSourceDisposedError: If this method is called on a disposed
            data source.
        """
        # TODO: Add a better API for this method.
        ...

    def __str__(self) -> str:
        return f"{self.id}::{self.name}"

    @classmethod
    def of_mapping(cls, mapping: Mapping[str, Any]) -> "DataSource":
        """
        Initialize and return a data source from a mapping describing it's
        state.

        :param mapping: A mapping that describes the state of a data source.

        :return: The initialized data source instance.
        """
        return cls(**mapping)


class UploadChunk(
    IdentifiableDomainObject,
    InitFromMapping,
    metaclass=ABCMeta,
):
    """An interface that represents part of an upload's content."""

    chunk_index: int
    chunk_content: Any

    def __str__(self) -> str:
        return "Chunk %d" % self.chunk_index

    @classmethod
    def of_mapping(cls, mapping: Mapping[str, Any]) -> "UploadChunk":
        """
        Initialize and return an upload chunk from a mapping describing it's
        state.

        :param mapping: A mapping that describes the state of an upload chunk
            instance.

        :return: The initialized upload chunk instance.
        """
        return cls(**mapping)


class UploadMetadata(
    Generic[_RT],
    ToTask[_RT, Sequence[bytes]],
    IdentifiableDomainObject,
    InitFromMapping,
    metaclass=ABCMeta,
):
    """An interface that defines a data upload to an IDR Server."""

    org_unit_code: str
    org_unit_name: str
    content_type: str

    @property
    @abstractmethod
    def extract_metadata(self) -> ExtractMetadata[Any, _RT]:
        """
        Return the :class:`extract metadata <ExtractMetadata>` instance that
        this upload metadata instance is associated to.

        :return: The extract metadata instance that this instance is associated
            to.
        """
        ...

    def get_upload_chunk_extra_init_kwargs(
        self,
    ) -> Mapping[str, Any] | None:
        """
        Return an optional mapping of extra keyword arguments to be used when
        initializing the :class:`upload chunk <UploadChunk>` instance
        associated with this upload metadata.

        :return: An optional mapping of extra keyword arguments to use when
            initializing the upload metadata instance associated with this
            upload.
        """
        return None

    @abstractmethod
    def to_task(self) -> Task[_RT, Sequence[bytes]]:
        """
        Return a :class:`task <Task>` instance that takes the extracted data
        as input and performs any processing/transformations that is required
        on the data, maps the data into a sequence of
        :class:`upload chunks <UploadChunk>` and returns the chunks.

        :return: A task instance used to process the extracted data and chunk
            it.
        """
        ...

    def __str__(self) -> str:
        return "Upload {} for extract {}".format(
            self.id,
            str(self.extract_metadata),
        )

    @classmethod
    def of_mapping(cls, mapping: Mapping[str, Any]) -> "UploadMetadata":
        """
        Initialize and return an upload metadata instance from a mapping
        describing it's state.

        :param mapping: A mapping that describes the state of an upload
            metadata instance.

        :return: The initialized upload metadata instance.
        """
        return cls(**mapping)

    @classmethod
    @abstractmethod
    def get_content_type(cls) -> str:
        """
        Return the content type of the final data to uploaded to the IDR
        Server after all transformations and processing has been done on the
        data.

        :return: The content type of the data to be uploaded to the IDR Server.
        """
        ...


class DataSourceType(AbstractDomainObject, metaclass=ABCMeta):
    """
    An interface representing the different kinds of supported data sources.
    """

    name: str
    description: str | None

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
        return f"{self.code}::{self.name}"

    @classmethod
    @abstractmethod
    def imp_data_source_klass(cls) -> type[DataSource]:
        """
        Return the :class:`DataSource` concrete implementation class for this
        data source type.

        :return: The ``DataSource`` implementation for this data source type.
        """
        ...

    @classmethod
    @abstractmethod
    def imp_extract_metadata_klass(cls) -> type[ExtractMetadata]:
        """
        Return the :class:`ExtractMetadata` concrete implementation class for
        this dats source type.

        :return: The ``ExtractMetadata`` implementation for this data source
            type.
        """
        ...

    @classmethod
    @abstractmethod
    def imp_upload_chunk_klass(cls) -> type[UploadChunk]:
        """
        Return the :class:`UploadChunk` concrete implementation class for this
        data source type.

        :return: The ``UploadChunk`` implementation for this data source type.
        """
        ...

    @classmethod
    @abstractmethod
    def imp_upload_metadata_klass(cls) -> type[UploadMetadata]:
        """
        Return the :class:`UploadMetadata` concrete implementation class for
        this data source type.

        :return: The ``UploadMetadata`` implementation for this data source
            type.
        """
        ...
