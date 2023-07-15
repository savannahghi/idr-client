from abc import ABCMeta, abstractmethod
from collections.abc import Mapping

from .base import DomainObject, IdentifiableDomainObject, NamedDomainObject

# =============================================================================
# METADATA INTERFACES
# =============================================================================


class MetadataObject(DomainObject, metaclass=ABCMeta):
    """Marker interface that identifies metadata containers.

    Define a :class:`DomainObject` that contains metadata. Metadata in this
    context refers to data that describes:

    * An operation to be performed by the client.
    * The resources needed as part of an operation to be performed.
    * Details of an operation that was performed by the client.
    * The data resulting from an operation performed by the client.
    """

    ...


class IdentifiableMetadataObject(
    MetadataObject,
    IdentifiableDomainObject,
    metaclass=ABCMeta,
):
    """A uniquely identifiable :class:`MetadataObject`."""

    ...


class DataSinkMetadata(
    NamedDomainObject,
    IdentifiableDomainObject,
    metaclass=ABCMeta,
):
    """:class:`Metadata<MetadataObject>` describing a :class:`DataSink`.

    This describes information used by the runtime to identify and/or
    initialize a `DataSink` to drain/upload to.
    """

    ...


class DataSourceMetadata(
    NamedDomainObject,
    IdentifiableDomainObject,
    metaclass=ABCMeta,
):
    """:class:`Metadata<MetadataObject>` describing a :class:`DataSource`.

    This describes information used by the runtime to identify and/or
    initialize a `DataSource` to draw/extract from. It defines a writable
    property, :attr:`draw_metadata` that holds a mapping of
    :class:`DrawMetadata` instances associated with the aforementioned
    `DataSource`.
    """

    @property
    @abstractmethod
    def draw_metadata(self) -> Mapping[str, "DrawMetadata"]:
        """Return a read only `Mapping` of :class:`DrawMetadata` instances.

        Specifically, return a read only `Mapping` of the known `DrawMetadata`
        instances that should be run against the :class:`DataSource` described
        by this instance.

        :return: A read only `Mapping` of the known `DrawMetadata` instances
            that should be run against the `DataSource` described by this
            instance.
        """
        ...

    @draw_metadata.setter
    @abstractmethod
    def draw_metadata(
        self,
        draw_metadata: Mapping[str, "DrawMetadata"],
    ) -> None:
        """Define a `Mapping` containing :class:`DrawMetadata` instances.

        Specifically, set this property with a read only `Mapping` of the known
        `DrawMetadata` instances that should be run against the
        :class:`DataSource` described by this instance.

        :param draw_metadata: A read only mapping containing the known
            `DrawMetadata` instances that should be run against the
            `DataSource` described by this instance.

        :return: None
        """
        ...


class DrawMetadata(
    NamedDomainObject,
    IdentifiableDomainObject,
    metaclass=ABCMeta,
):
    """:class:`Metadata<MetadataObject>` describing what to draw/extract.

    This interface defines metadata describing data to be drawn/extracted from
    a :class:`DataSource`. Each `DrawMetadata` has an *owning*
    :class:`DataSourceMetadata` instance that describes the :class:`DataSource`
    on which the draw should be performed on. Conversely, a single
    `DataSourceMetadata` can have multiple `DrawMetadata` instances associated
    with it.

    A read-only property, :attr:`data_source_metadata` is provided to allow
    access to the *owning* `DataSourceMetadata` instance.
    """

    @property
    @abstractmethod
    def data_source_metadata(self) -> DataSourceMetadata:
        """Return a reference to the owning :class:`DataSourceMetadata`.

        Return a reference to the `DataSourceMetadata` that describes
        the :class:`DataSource` that this extract should be run against.

        :return: A reference to the owning `DataSourceMetadata` of this
            instance.
        """
        ...


class DrainMetadata(IdentifiableMetadataObject, metaclass=ABCMeta):
    """:class:`Metadata <MetadataObject>` describing a drain/upload data.

    This interface describes the details of :class:`clean data<CleanedData>`
    that can be drained/uploaded to a :class:`DataSink`. This includes the
    :class:`DrawMetadata` instance that describes the source data.

    A read-only property, :attr:`draw_metadata` is provided to allow the access
    of the `DrawMetadata` instance that led to the said data being drawn from
    the source.
    """

    @property
    @abstractmethod
    def draw_metadata(self) -> DrawMetadata:
        """Return the :class:`DrawMetadata` instance that describes the source
        data.

        :return: The draw metadata instance that describes the source data.
        """
        ...
